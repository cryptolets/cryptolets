"""
Choose which designs are worth synthesizing.

Synthesis costs far more than the high level run that estimated every design, so
a sweep can ask for only the designs on the area and latency frontier. The
estimate decides, which is the price of not synthesizing everything.
"""
import logging
from pathlib import Path

import yaml

from tessera.helper import get_design_dir_name


def latency_time(row):
    """
    How long the design takes, in nanoseconds.

    Cycles alone do not compare two designs, since one clocked slower does more
    in each. This is the target period rather than what synthesis achieved,
    because the ranking happens before synthesis runs.
    """
    if row.get("latency"):
        return row["latency"] * row["period"]

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
    The rows worth synthesizing, one frontier per kernel_key.

    Only designs that compute the same thing are compared, since a design built
    for a different bitwidth or field is another unit rather than a cheaper way
    of building this one.
    """
    if mode == "all":
        return rows

    units = {}
    for row in rows:
        units.setdefault(tuple(row.get(k) for k in kernel_key), []).append(row)

    return [row for unit in units.values() for row in frontier(unit, mode)]


def select_designs(designs, kernel_build_dir, mode, kernel_key):
    "The sweep's designs, narrowed to the ones worth synthesizing"
    if mode == "all":
        return designs

    if not kernel_key:
        raise Exception(
            f"'{mode}' only compares designs that compute the same thing, so "
            f"the kernel needs a kernel_key in its kernel.yaml")

    # What the design is worth is in its package, so one Catapult has not
    # built yet cannot be ranked and is left out
    ranked = []
    for design in designs:
        manifest_path = Path(kernel_build_dir, get_design_dir_name(design),
                             "package", "manifest.yaml")
        if manifest_path.exists():
            manifest = yaml.safe_load(manifest_path.read_text())
            ranked.append({**design, **{k: manifest.get(k)
                                        for k in ("area", "delay", "latency")}})

    selected = select(ranked, mode, kernel_key)
    logging.info(f"Synthesizing {len(selected)} of {len(designs)} designs ({mode})")
    for design in selected:
        logging.info(f"  {get_design_dir_name(design)}")

    # The metrics were only for ranking, so each design goes on as the sweep had it
    return [{k: v for k, v in design.items()
             if k not in ("area", "delay", "latency")} for design in selected]
