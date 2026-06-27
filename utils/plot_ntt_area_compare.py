#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_ntt_area_compare_svg_legacy import (
    COMPARE_CATEGORIES,
    build_rows,
    load_sweep,
    write_csv,
)


COLORS = {
    "baseline": "#4C78A8",
    "compare": "#F58518",
}
FONT = {
    "title": 24,
    "axis": 22,
    "tick": 18,
    "legend": 18,
    "bar": 14,
    "group": 18,
}


def fmt_area(value):
    if value >= 100000:
        return f"{value / 1000.0:.1f}k"
    if value >= 1000:
        return f"{value / 1000.0:.2f}k"
    return f"{value:.1f}"


def grouped_rows(rows):
    by_unroll = {}
    for row in rows:
        by_unroll.setdefault((row["ntt_len"], row["unroll"]), {})[row["category"]] = row

    groups = []
    for key in sorted(by_unroll):
        category_rows = by_unroll[key]
        groups.extend(category_rows[category] for category in COMPARE_CATEGORIES if category in category_rows)
    return groups


def write_plot(path, rows, baseline_label, compare_label):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = grouped_rows(rows)

    bar_width = 0.32
    category_gap = 0.9
    unroll_gap = 1.35
    x_positions = []
    x = 0.0
    prev_unroll = None
    unroll_ranges = []
    unroll_start = None

    for row in rows:
        if prev_unroll is None:
            unroll_start = x
        elif row["unroll"] != prev_unroll:
            unroll_ranges.append((prev_ntt_len, prev_unroll, unroll_start, x - category_gap))
            x += unroll_gap
            unroll_start = x

        x_positions.append(x)
        x += 2 * bar_width + category_gap
        prev_ntt_len = row["ntt_len"]
        prev_unroll = row["unroll"]

    if prev_unroll is not None:
        unroll_ranges.append((prev_ntt_len, prev_unroll, unroll_start, x - category_gap))

    max_norm = max(max(row["baseline_norm"], row["compare_norm"]) for row in rows)
    y_max = max(1.4, max_norm * 1.22)
    fig_width = max(18.0, 1.0 * len(rows) + 5.0)
    fig, ax = plt.subplots(figsize=(fig_width, 6.8))

    baseline_x = [x - bar_width / 2 for x in x_positions]
    compare_x = [x + bar_width / 2 for x in x_positions]
    baseline_vals = [row["baseline_norm"] for row in rows]
    compare_vals = [row["compare_norm"] for row in rows]

    baseline_bars = ax.bar(
        baseline_x,
        baseline_vals,
        width=bar_width,
        color=COLORS["baseline"],
        label=baseline_label,
    )
    compare_bars = ax.bar(
        compare_x,
        compare_vals,
        width=bar_width,
        color=COLORS["compare"],
        label=compare_label,
    )

    label_offset = y_max * 0.012
    for bars, area_key in [(baseline_bars, "baseline_area"), (compare_bars, "compare_area")]:
        for bar, row in zip(bars, rows):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + label_offset,
                fmt_area(row[area_key]),
                ha="center",
                va="bottom",
                fontsize=FONT["bar"],
                rotation=90,
            )

    category_labels = [row["category"].replace("Control Logic", "Control\nLogic") for row in rows]
    ax.set_xticks(x_positions)
    ax.set_xticklabels(category_labels, fontsize=FONT["tick"])
    ax.set_ylabel("Normalized area (KL-DIF = 1)", fontsize=FONT["axis"], fontweight="bold")
    ax.set_title("NTT Area Comparison Normalized To KL-DIF", fontsize=FONT["title"], fontweight="bold", pad=18)
    ax.tick_params(axis="y", labelsize=FONT["tick"])
    ax.grid(axis="y", color="#e6e6e6", linewidth=1)
    ax.set_axisbelow(True)
    ax.set_ylim(0, y_max)
    ax.margins(x=0.01)

    for ntt_len, unroll, start, end in unroll_ranges:
        center = (start + end) / 2
        ax.text(
            center,
            -0.18,
            f"N={ntt_len}, u={unroll}",
            ha="center",
            va="top",
            fontsize=FONT["group"],
            fontweight="bold",
            transform=ax.get_xaxis_transform(),
        )

    legend = ax.legend(
        # title="Design",
        fontsize=FONT["legend"],
        title_fontsize=FONT["legend"],
        ncol=2,
        loc="upper right",
        # bbox_to_anchor=(1.01, 1.0),
        frameon=False,
    )
    legend._legend_box.align = "left"
    # ax.text(
    #     1.01,
    #     0.72,
    #     "Bar labels are raw area\nKL-DIF is normalized to 1",
    #     transform=ax.transAxes,
    #     ha="left",
    #     va="top",
    #     fontsize=11,
    # )

    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.22, top=0.88)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Compare two NTT sweeps by area category, normalized to the baseline sweep.")
    parser.add_argument("--baseline-configs", required=True, help="Baseline sweep config JSON, e.g. KL-DIF.")
    parser.add_argument("--compare-configs", required=True, help="Comparison sweep config JSON, e.g. Stockham DIT.")
    parser.add_argument("--catapult-dir", default="lvl2/ntt/Catapult")
    parser.add_argument("--baseline-label", default=None)
    parser.add_argument("--compare-label", default=None)
    parser.add_argument("--out-csv", default="lvl2/ntt/Catapult/ntt_area_compare.csv")
    parser.add_argument("--out-png", default="lvl2/ntt/Catapult/ntt_area_compare.png")
    args = parser.parse_args()

    baseline_suffix, baseline_configs = load_sweep(args.baseline_configs)
    compare_suffix, compare_configs = load_sweep(args.compare_configs)
    rows = build_rows(baseline_configs, baseline_suffix, compare_configs, compare_suffix, args.catapult_dir)
    if not rows:
        raise SystemExit("No matched rtl.rpt area data found for these sweeps.")

    baseline_label = args.baseline_label or rows[0]["baseline_label"]
    compare_label = args.compare_label or rows[0]["compare_label"]

    write_csv(Path(args.out_csv), rows)
    write_plot(Path(args.out_png), rows, baseline_label, compare_label)
    print(f"Wrote {args.out_png}")
    print(f"Wrote {args.out_csv}")


if __name__ == "__main__":
    main()
