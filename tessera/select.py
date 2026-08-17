"""
Choose which designs for logic synthesizing.
"""
import logging
from pathlib import Path

import yaml

from tessera.helper import get_design_dir_name


def latency_time(row):
    if row.get("latency"):
        return row["latency"] * row["design"]["period"]

    # A combinational design finishes within one cycle, so its delay is the time
    return row.get("delay")


def frontier(rows, mode):
    "The designs that no other design beats on both area and time"
    ranked = [row for row in rows
              if row.get("area") is not None and latency_time(row) is not None]

    # Smallest first, so a design belongs when nothing before it was also faster
    best, fastest = [], float("inf")
    for row in sorted(ranked, key=lambda r: (r["area"], latency_time(r))):
        if latency_time(row) <= fastest:
            best.append(row)
            fastest = latency_time(row)

    if mode == "pareto":
        return best

    # Sorted by area, so the ends are the smallest and the fastest
    return best[:1] if len(best) < 2 else [best[0], best[-1]]


def select(rows, mode, kernel_key):
    """
    Select the rows worth synthesizing.
    """
    if mode == "all":
        return rows

    units = {}
    for row in rows:
        units.setdefault(tuple(row["design"].get(k) for k in kernel_key), []).append(row)

    return [row for unit in units.values() for row in frontier(unit, mode)]


def select_designs(designs, kernel, kernel_build_dir, mode, kernel_key):
    "The sweep's designs, narrowed to the ones worth synthesizing"
    if mode == "all":
        return designs

    if not kernel_key:
        raise Exception(
            f"'{mode}' only compares designs that compute the same thing, so "
            f"the kernel needs a kernel_key in its kernel.yaml")

    # What the design is worth is in its package, so one Catapult has not
    # built yet cannot be ranked and is left out. The metrics sit beside the
    # design rather than in it, since a design is only its parameters.
    ranked = []
    for design in designs:
        manifest_path = Path(kernel_build_dir, get_design_dir_name(design, kernel),
                             "package", "manifest.yaml")
        if manifest_path.exists():
            manifest = yaml.safe_load(manifest_path.read_text())
            ranked.append({"design": design,
                           **{k: manifest.get(k) for k in ("area", "delay", "latency")}})

    selected = [row["design"] for row in select(ranked, mode, kernel_key)]
    logging.info(f"Synthesizing {len(selected)} of {len(designs)} designs ({mode})")
    for design in selected:
        logging.info(f"  {get_design_dir_name(design, kernel)}")

    return selected
