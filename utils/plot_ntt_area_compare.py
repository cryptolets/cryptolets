#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


RAW_AREA_CATEGORIES = ["MUX", "FUNC", "LOGIC", "BUFFER", "MEM", "ROM", "REG", "FSM-REG", "FSM-COMB"]
AREA_BUCKETS = {
    "Control Logic": ["MUX", "LOGIC", "FSM-COMB"],
    "Datapath": ["FUNC"],
    "Memory": ["BUFFER", "MEM", "ROM"],
    "Reg": ["REG", "FSM-REG"],
}
COMPARE_CATEGORIES = ["Reg", "Datapath", "Control Logic", "Total"]
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


def design_label(cfg):
    variant = cfg.get("NTT_CONSTANT_GEOMETRY_VARIANT") or cfg.get("NTT_STOCKHAM_VARIANT") or cfg.get("NTT_IMPL", "")
    return {
        "NTT_KORN_LAMBIOTTE_DIF": "KL-DIF",
        "NTT_KORN_LAMBIOTTE_DIT": "KL-DIT",
        "NTT_STOCKHAM_DIF": "ST-DIF",
        "NTT_STOCKHAM_DIT": "ST-DIT",
    }.get(variant, variant)


def variant_tokens(cfg):
    impl = cfg.get("NTT_IMPL", "")
    variant = cfg.get("NTT_CONSTANT_GEOMETRY_VARIANT") or cfg.get("NTT_STOCKHAM_VARIANT") or ""
    tokens = []

    if impl == "NTT_IMPL_CONSTANT_GEOMETRY":
        tokens.append("__ni_cg__")
        tokens_by_variant = {
            "NTT_KORN_LAMBIOTTE_DIF": "__ncgv_kldif__",
            "NTT_KORN_LAMBIOTTE_DIT": "__ncgv_kldit__",
            "NTT_PEASE_DIF": "__ncgv_pdif__",
            "NTT_PEASE_DIT": "__ncgv_pdit__",
        }
        if variant in tokens_by_variant:
            tokens.append(tokens_by_variant[variant])
    elif impl == "NTT_IMPL_STOCKHAM":
        tokens.append("__ni_stock__")
        tokens_by_variant = {
            "NTT_STOCKHAM_DIF": "__nstk_dif__",
            "NTT_STOCKHAM_DIT": "__nstk_dit__",
        }
        if variant in tokens_by_variant:
            tokens.append(tokens_by_variant[variant])
    elif impl == "NTT_IMPL_STANDARD":
        tokens.append("__ni_std__")

    tokens.extend(
        [
            "__nl_{}__".format(cfg.get("NTT_LEN")),
            "__NTT_BF_UNROLL_{}__".format(cfg.get("NTT_BF_UNROLL")),
            "__bw_{}__".format(cfg.get("BITWIDTH")),
        ]
    )
    return tokens


def match_key(cfg):
    return (
        cfg.get("NTT_LEN"),
        cfg.get("NTT_BF_UNROLL"),
    )


def load_sweep(path):
    data = json.loads(Path(path).read_text())
    return data.get("control_flags", {}).get("PROJECT_NAME_SUFFIX", ""), data.get("sweep_configs", [])


def latest_solution_rpt(project_dir):
    candidates = []
    for rpt in project_dir.glob("ntt.v*/rtl.rpt"):
        match = re.search(r"ntt\.v(\d+)", str(rpt))
        version = int(match.group(1)) if match else -1
        candidates.append((version, rpt))
    return max(candidates, default=(None, None))[1]


def find_project_dir(catapult_dir, cfg, suffix):
    catapult_dir = Path(catapult_dir)
    tokens = variant_tokens(cfg)
    matches = []

    for project_dir in catapult_dir.glob("Catapult_*"):
        if not project_dir.is_dir() or project_dir.name.endswith(".ccs"):
            continue
        name = project_dir.name
        if suffix and not name.endswith("__{}".format(suffix)):
            continue
        if all(token in name for token in tokens):
            matches.append(project_dir)

    matches.sort(key=lambda path: (latest_solution_rpt(path) is not None, path.stat().st_mtime), reverse=True)
    return matches[0] if matches else None


def parse_post_assignment_area(rpt_path):
    values = {}
    in_area_scores = False

    for line in rpt_path.read_text(errors="replace").splitlines():
        if line.strip() == "Area Scores":
            in_area_scores = True
            continue
        if not in_area_scores:
            continue

        match = re.match(r"\s*(Total Area Score|MUX|FUNC|LOGIC|BUFFER|MEM|ROM|REG|FSM-REG|FSM-COMB):\s+(.*)$", line)
        if not match:
            continue

        name, rest = match.groups()
        rest_without_reported_pcts = re.sub(r"\([^)]*\)", "", rest)
        nums = re.findall(r"\d+(?:\.\d+)?", rest_without_reported_pcts)
        if len(nums) >= 3:
            values[name] = float(nums[-1])

    total = values.get("Total Area Score", 0.0)
    areas = {name: values.get(name, 0.0) for name in RAW_AREA_CATEGORIES}
    return total, areas


def bucket_areas(raw_areas):
    return {
        bucket: sum(raw_areas.get(raw_name, 0.0) for raw_name in raw_names)
        for bucket, raw_names in AREA_BUCKETS.items()
    }


def read_area_row(catapult_dir, cfg, suffix):
    project_dir = find_project_dir(catapult_dir, cfg, suffix)
    if not project_dir:
        print(
            "[missing] no Catapult project matching {} NTT_LEN={} NTT_BF_UNROLL={}".format(
                design_label(cfg),
                cfg.get("NTT_LEN"),
                cfg.get("NTT_BF_UNROLL"),
            )
        )
        return None

    rpt = latest_solution_rpt(project_dir)
    if not rpt:
        print("[missing] {}/ntt.v*/rtl.rpt".format(project_dir))
        return None

    total, raw_areas = parse_post_assignment_area(rpt)
    if total <= 0:
        print("[skip] no post-assignment area found: {}".format(rpt))
        return None

    buckets = bucket_areas(raw_areas)
    project_name = project_dir.name
    sweep_key = project_name[len("Catapult_") :] if project_name.startswith("Catapult_") else project_name
    return {
        "cfg": cfg,
        "label": design_label(cfg),
        "sweep_key": sweep_key,
        "rtl_rpt": str(rpt),
        "areas": {
            "Reg": buckets["Reg"],
            "Datapath": buckets["Datapath"],
            "Control Logic": buckets["Control Logic"],
            "Total": total,
        },
    }


def build_rows(baseline_configs, baseline_suffix, compare_configs, compare_suffix, catapult_dir):
    baseline_by_key = {match_key(cfg): cfg for cfg in baseline_configs}
    compare_by_key = {match_key(cfg): cfg for cfg in compare_configs}
    rows = []

    for key in sorted(set(baseline_by_key) & set(compare_by_key)):
        baseline = read_area_row(catapult_dir, baseline_by_key[key], baseline_suffix)
        compare = read_area_row(catapult_dir, compare_by_key[key], compare_suffix)
        if not baseline or not compare:
            continue

        ntt_len, unroll = key
        for category in COMPARE_CATEGORIES:
            baseline_area = baseline["areas"][category]
            compare_area = compare["areas"][category]
            if baseline_area <= 0:
                baseline_norm = 0.0
                compare_norm = 0.0
            else:
                baseline_norm = 1.0
                compare_norm = compare_area / baseline_area

            rows.append(
                {
                    "ntt_len": ntt_len,
                    "unroll": unroll,
                    "category": category,
                    "baseline_label": baseline["label"],
                    "compare_label": compare["label"],
                    "baseline_area": baseline_area,
                    "compare_area": compare_area,
                    "baseline_norm": baseline_norm,
                    "compare_norm": compare_norm,
                    "baseline_sweep_key": baseline["sweep_key"],
                    "compare_sweep_key": compare["sweep_key"],
                    "baseline_rtl_rpt": baseline["rtl_rpt"],
                    "compare_rtl_rpt": compare["rtl_rpt"],
                }
            )

    return rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ntt_len",
        "unroll",
        "category",
        "baseline_label",
        "compare_label",
        "baseline_area",
        "compare_area",
        "baseline_norm",
        "compare_norm",
        "baseline_sweep_key",
        "compare_sweep_key",
        "baseline_rtl_rpt",
        "compare_rtl_rpt",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            for key in ["baseline_area", "compare_area", "baseline_norm", "compare_norm"]:
                out[key] = "{:.3f}".format(float(out[key]))
            writer.writerow(out)


def fmt_area(value):
    if value >= 100000:
        return "{:.1f}k".format(value / 1000.0)
    if value >= 1000:
        return "{:.2f}k".format(value / 1000.0)
    return "{:.1f}".format(value)


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
    category_gap = 0.2
    unroll_gap = 0.65
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
    y_max = max(1.5, max_norm * 1.22)
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

    category_labels = [
        row["category"].replace("Datapath", "Data\npath").replace("Control Logic", "Control\nLogic")
        for row in rows
    ]
    ax.set_xticks(x_positions)
    ax.set_xticklabels(category_labels, fontsize=FONT["tick"])
    ax.set_ylabel("Normalized area (KL-DIF = 1)", fontsize=FONT["axis"], fontweight="bold")
    ax.set_title("NTT Compute Area Normalized To KL-DIF", fontsize=FONT["title"], fontweight="bold", pad=18)
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
            "N={}, u={}".format(ntt_len, unroll),
            ha="center",
            va="top",
            fontsize=FONT["group"],
            fontweight="bold",
            transform=ax.get_xaxis_transform(),
        )

    legend = ax.legend(
        fontsize=FONT["legend"],
        title_fontsize=FONT["legend"],
        ncol=2,
        loc="upper right",
        bbox_to_anchor=(1.0, 1.02),
        frameon=False,
    )
    legend._legend_box.align = "left"

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
    print("Wrote {}".format(args.out_png))
    print("Wrote {}".format(args.out_csv))


if __name__ == "__main__":
    main()
