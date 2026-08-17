"""
Collect what a sweep measured, as one row per design.

Every stage records its results in the design's manifest, so a sweep is read by
gathering those files. A design that has not been through a stage yet leaves
those columns empty.
"""
import csv
from pathlib import Path

import yaml

# The order results are shown in, after the parameters that the sweep varied
METRICS = ["latency", "area", "area (mm^2)", "delay",
           "luts", "ffs", "dsps", "brams", "carry",
           "power", "power_dc"]


def collect(kernel_build_dir):
    "One row per design, holding its parameters and what each stage measured"
    rows = []
    for manifest_path in sorted(Path(kernel_build_dir).glob("*/package/manifest.yaml")):
        manifest = yaml.safe_load(manifest_path.read_text())

        row = dict(manifest.get("params", {}))
        for metric in ("latency", "area", "delay",
                       "luts", "ffs", "dsps", "brams", "carry"):
            row[metric] = manifest.get(metric)

        area = manifest.get("area")
        row["area (mm^2)"] = area / 1e6 if area else None

        # Both are the whole design's power, one estimated and one measured
        for key in ("power", "power_dc"):
            measured = manifest.get(key)
            row[key] = measured["total"] if measured else None

        rows.append(row)

    return rows


def where(rows, filters):
    """
    Keep the rows whose parameters match, as {name: value}.

    A value is compared as a number when both sides read as one, so --where
    period=1 matches a design built at 1.0.
    """
    for name, wanted in filters.items():
        rows = [row for row in rows if _matches(row.get(name), wanted)]
    return rows


def _matches(value, wanted):
    try:
        return float(value) == float(wanted)
    except (TypeError, ValueError):
        return str(value) == str(wanted)


def drop_empty_columns(rows):
    "Hide what the sweep did not vary or has not measured yet"
    if not rows:
        return rows

    keep = [k for k in rows[0] if any(row.get(k) is not None for row in rows)]
    return [{k: row[k] for k in keep} for row in rows]


def order_columns(rows):
    "Parameters first, since they say which design a row is, then its results"
    if not rows:
        return rows

    params = [k for k in rows[0] if k not in METRICS]
    order = [*params, *[m for m in METRICS if m in rows[0]]]
    return [{k: row[k] for k in order if k in row} for row in rows]


def _format(key, value):
    if value is None:
        return ""
    if key in ("power", "power_dc"):
        return f"{value:.2e}"
    if key == "area (mm^2)":
        return f"{value:.3f}"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def table(rows):
    "The rows as aligned text, with numbers to the right of their column"
    if not rows:
        return "No designs"

    keys = list(rows[0].keys())
    widths = {k: max(len(k), *(len(_format(k, row[k])) for row in rows)) for k in keys}

    lines = [
        " | ".join(f"{k:<{widths[k]}}" for k in keys),
        "-+-".join("-" * widths[k] for k in keys),
    ]
    for row in rows:
        lines.append(" | ".join(
            f"{_format(k, row[k]):>{widths[k]}}" if isinstance(row[k], (int, float))
            else f"{_format(k, row[k]):<{widths[k]}}"
            for k in keys))

    return "\n".join(lines)


def write_csv(rows, path):
    "The rows as they are, so a plot reads the numbers rather than the table"
    if not rows:
        return

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
