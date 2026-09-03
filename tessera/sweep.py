"""
Expand a sweep config into concrete designs.

A sweep is the cartesian product of its parameters, then:
  - derivations rewrite a design when one parameter decides another
  - filters drop designs that are invalid or duplicate another design

Add a rule by writing a function and listing it in DERIVATIONS or FILTERS.
"""
import json
import logging
from itertools import product

from tessera.models.common import load_curves
from tessera.models.design import Design
from tessera.const import ARB_FIELD


# --- derivations: (design) -> None, edited in place ---

def derive_curve_width(design):
    "A named curve fixes n to the bitwidth of its field."
    curve = design.get("curve")
    if not curve or curve == ARB_FIELD:
        return
    field = load_curves()[curve].get(design.get("field", "base"))
    if field:
        design["bitwidth"] = field["bitwidth"]


def derive_arb_field_field(design):
    "An arb_field prime is not tied to a curve, so it has only a base field."
    if design.get("curve") == ARB_FIELD:
        design["field"] = "base"


DERIVATIONS = [derive_curve_width, derive_arb_field_field]

# --- filters: (design) -> reason to skip, or None to keep ---

def filter_missing_field(design):
    "Curves without a scalar field cannot be swept over one."
    curve = design.get("curve")
    if not curve or curve == ARB_FIELD:
        return None
    field = design.get("field", "base")
    if field not in load_curves()[curve]:
        return f"curve '{curve}' has no {field} field"
    return None


def filter_arb_field_fixed_q(design):
    """
    An arb_field prime is random, so we only use it to test
    variable parameters, and no point in fixing it.
    """
    if design.get("curve") == ARB_FIELD and design.get("q_type") == "fixed_q":
        return "arb_field has no meaningful fixed modulus"
    return None


FILTERS = [filter_missing_field, filter_arb_field_fixed_q]

# Params keyed by n rather than swept directly
WIDTH_MAPS = ("base_mul_width", "kar_base_mul_width")

def _apply_width_maps(sweep, design):
    "Expand the n-keyed width maps into one design per combination."
    n = design["bitwidth"]
    lists = [(sweep.get(name) or {}).get(n, [None]) for name in WIDTH_MAPS]

    for values in product(*lists):
        out = dict(design)
        for name, value in zip(WIDTH_MAPS, values):
            if value is not None:
                out[name] = value

        # A multiplier that never splits down to a width does not sweep it, so
        # pinning it to the full width collapses those designs onto one
        mul_type = out.get("mul_type")
        if mul_type in ("mul_nor", "mul_sb") and "kar_base_mul_width" in out:
            out["kar_base_mul_width"] = n
        if mul_type == "mul_nor" and "base_mul_width" in out:
            out["base_mul_width"] = n

        # Karatsuba recurses down to its base width, then schoolbook takes over
        # and recurses to its own. Stopping karatsuba below that does nothing.
        kar, base = out.get("kar_base_mul_width"), out.get("base_mul_width")
        if kar is not None and base is not None and kar < base:
            continue

        yield out


def flatten_sweep(sweep, path, reuse=False):
    """
    Expand a sweep config into a list of designs
    """

    # Reuse an existing flattened sweep stored in json file
    if reuse:
        if not path.exists():
            raise Exception(f"No stored sweep at {path}. "
                            f"Run from the first stage to create it.")
        stored = json.loads(path.read_text())["sweep"]
        return [Design(d) for d in stored]

    # A parameter the sweep leaves out is not part of any design, so a kernel
    # that has no use for it carries nothing for it either
    keys = [k for k in sweep if k not in WIDTH_MAPS and sweep[k] is not None]
    designs, seen, skipped = [], set(), {}

    for combo in product(*(sweep[k] for k in keys)):
        design = dict(zip(keys, combo))

        for derive in DERIVATIONS:
            derive(design)

        reason = next((r for f in FILTERS if (r := f(design))), None)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue

        for out in _apply_width_maps(sweep, design):
            # Derivations can collapse distinct combinations onto one design
            key = tuple(sorted(out.items()))
            if key not in seen:
                seen.add(key)
                designs.append(Design(out))

    for reason, count in skipped.items():
        logging.warning(f"Skipped {count} design(s): {reason}")

    path.write_text(json.dumps({"sweep": [d.get_design() for d in designs]}, indent=2))
    return designs


def unflatten_sweep(flattened_sweep):
    sweep_config = {}
    for design in flattened_sweep:
        for k, v in design.items():
            sweep_config.setdefault(k, [])
            if v not in sweep_config[k]:
                sweep_config[k].append(v)
    return sweep_config
