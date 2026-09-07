"""
Resolve the field a design works over.

A design names a curve and one of its fields, or arb_field for a random
prime of the requested bitwidth.
"""
from sympy import randprime
from sympy.core.random import seed as sympy_seed

from reference.redc import barrett_get_mu, mont_get_q_prime, to_mont
from tessera.models.common import load_curves
from tessera.const import ARB_FIELD

SEED = 42
FIELD_CONSTANTS = ("q",) # constant kernel parameters
ARB_COEFFS = {"a": "0", "b": "1", "d": "2"}


def get_modulus(design, seed=SEED):
    curve = design.get("curve", ARB_FIELD)
    if curve != ARB_FIELD:
        return int(curves()[curve][design.get("field", "base")]["q"], 16)

    bitwidth = design["bitwidth"]
    sympy_seed(seed)
    return randprime(1 << (bitwidth - 1), (1 << bitwidth) - 1)


def design_fields(design):
    """
    Generated Field (with prime modulus, bitwidth, etc.) descriptors into params.h
    """
    curve = design.get("curve", ARB_FIELD)
    field = design.get("field", "base")
    name = curve if curve == ARB_FIELD else f"{curve}_{field}"

    q = get_modulus(design)
    return [{
        "name": name,
        "bitwidth": design["bitwidth"],
        "q": f"{q:x}",
        # A constant multiplier bakes one of these in
        "q_prime": f"{mont_get_q_prime(q):x}",
        "mu": f"{barrett_get_mu(q):x}",
        **curve_coeffs(curve, q, design.get("mred") == "mred_mont"),
    }]


def curve_coeffs(curve, q, mont):
    """
    The curve's own constants, which the point operations multiply by.

    A montgomery design works in its own domain, so it holds them converted.
    """
    # An arb_field is not a real curve, so its coefficients are only there to
    # give a design something to multiply by
    known = ARB_COEFFS if curve == ARB_FIELD else curves()[curve]

    out = {}
    for name in ("a", "b", "d"):
        if name in known:
            value = int(known[name], 16) % q
            out[name] = f"{to_mont(value, q) if mont else value:x}"

    # The twisted edwards addition reads 2d, so it is precomputed
    if "d" in known:
        k = (2 * int(known["d"], 16)) % q
        out["k"] = f"{to_mont(k, q) if mont else k:x}"
    return out
