"""
Choose which designs for logic synthesizing.
"""
import logging

import yaml


def latency_time(row):
    if row.get("latency"):
        return row["latency"] * row["design"].design["period"]
    # A combinational design finishes within one cycle, so its delay is the time
    return row.get("delay")


def pareto_frontier(rows, mode):
    """
    Get designs which are on the Pareto frontier (area vs latency)
    """
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


def select_rows(rows, mode, kernel_key):
    """
    Select the rows worth synthesizing.
    """
    if mode == "all": return rows

    units = {}
    for row in rows:
        units.setdefault(tuple(row["design"].design.get(k) for k in kernel_key), []).append(row)

    return [row for unit in units.values() for row in pareto_frontier(unit, mode)]


def select_designs(designs, kernel, mode):
    """
    The sweep's designs, narrowed to the ones worth synthesizing
    """
    if mode == "all":
        return designs

    kernel_key = kernel.config.kernel_key
    if not kernel_key:
        raise Exception(
            f"'{mode}' only compares designs that compute the same thing, so "
            f"the kernel needs a kernel_key in its kernel.yaml")

    # What a design is worth is in its package, written by the Catapult step
    ranked = []
    for design in designs:
        manifest = yaml.safe_load((design.build_dir / "package" / "manifest.yaml").read_text())
        ranked.append({"design": design,
                       **{k: manifest.get(k) for k in ("area", "delay", "latency")}})

    selected = [row["design"] for row in select_rows(ranked, mode, kernel_key)]
    logging.info(f"Synthesizing {len(selected)} of {len(designs)} designs ({mode})")
    for design in selected:
        logging.info(f"  {design.build_dir.name}")

    return selected
