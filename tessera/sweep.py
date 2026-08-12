"""
Expand a sweep config into concrete designs.

A sweep is the cartesian product of its parameters, then:
  - derivations rewrite a design when one parameter decides another
  - filters drop designs that are invalid or duplicate another design

Add a rule by writing a function and listing it in DERIVATIONS or FILTERS.
"""
import logging
from itertools import product

from tessera.config import ARB_CURVE, curves


# --- derivations: (design) -> None, edited in place ---

def derive_curve_width(design):
    "A named curve fixes n to the bitwidth of its field."
    curve = design.get("curve")
    if not curve or curve == ARB_CURVE:
        return
    field = curves()[curve].get(design.get("field", "base"))
    if field:
        design["bitwidth"] = field["bitwidth"]



DERIVATIONS = [derive_curve_width]


# --- filters: (design) -> reason to skip, or None to keep ---

def filter_missing_field(design):
    "Curves without a scalar field cannot be swept over one."
    curve = design.get("curve")
    if not curve or curve == ARB_CURVE:
        return None
    field = design.get("field", "base")
    if field not in curves()[curve]:
        return f"curve '{curve}' has no {field} field"
    return None


def filter_arb_curve_fixed_q(design):
    """
    An arb_curve prime is random, so we only use it to test
    variable parameters, and no point in fixing it.
    """
    if design.get("curve") == ARB_CURVE and design.get("q_type") == "fixed_q":
        return "arb_curve has no meaningful fixed modulus"
    return None


FILTERS = [filter_missing_field, filter_arb_curve_fixed_q]

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
        yield out


def flatten_sweep(sweep):
    "Expand a sweep config into a list of designs."
    keys = [k for k in sweep if k not in WIDTH_MAPS]
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
                designs.append(out)

    for reason, count in skipped.items():
        logging.warning(f"Skipped {count} design(s): {reason}")

    return designs


def unflatten_sweep(flattened_sweep):
    sweep_config = {}
    for design in flattened_sweep:
        for k, v in design.items():
            sweep_config.setdefault(k, [])
            if v not in sweep_config[k]:
                sweep_config[k].append(v)
    return sweep_config
