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
METRICS = ["cycles", "latency", "area (um^2)", "area (mm^2)",
           "delay", "delay_dc",
           "luts", "ffs", "dsps", "brams", "carry",
           "power (uW)", "power_dc (uW)"]

# What a column is called, and what its value is scaled by to suit that name
UNITS = {
    "latency": ("cycles", 1),
    "area": ("area (um^2)", 1),
    "period": ("period", 1),
    "dep_period_ratio": ("dpr", 1),
    "power": ("power (uW)", 1e6),
    "power_dc": ("power_dc (uW)", 1e6),
}


def collect(kernel_build_dir):
    "One row per design, holding its parameters and what each stage measured"
    rows = []
    for manifest_path in sorted(Path(kernel_build_dir).glob("*/package/manifest.yaml")):
        manifest = yaml.safe_load(manifest_path.read_text())

        row = {}
        for name, value in manifest.get("params", {}).items():
            label, scale = UNITS.get(name, (name, 1))
            row[label] = value * scale if isinstance(value, (int, float)) else value

        for metric in ("latency", "area"):
            label, scale = UNITS[metric]
            value = manifest.get(metric)
            row[label] = value * scale if value is not None else None

        # What the high level run estimated, and what synthesis achieved
        row["delay"] = manifest.get("delay")
        row["delay_dc"] = manifest.get("delay_dc")

        # A sequential design takes its cycles at the clock it was built for
        cycles, period = manifest.get("latency"), manifest["params"]["period"]
        row["latency"] = cycles * period if cycles else manifest.get("delay")

        for metric in ("luts", "ffs", "dsps", "brams", "carry"):
            row[metric] = manifest.get(metric)

        area = manifest.get("area")
        row["area (mm^2)"] = area / 1e6 if area else None

        # Both are the whole design's power, one estimated and one measured
        for key in ("power", "power_dc"):
            label, scale = UNITS[key]
            measured = manifest.get(key)
            row[label] = measured["total"] * scale if measured else None

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
    if key.startswith("power"):
        return f"{value:.2f}"
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
