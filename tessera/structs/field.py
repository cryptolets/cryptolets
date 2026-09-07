"""
Build the struct for a field: its modulus and every constant computed from it.
"""
from functools import lru_cache

from sympy import randprime
from sympy.core.random import seed as sympy_seed

from reference.redc import barrett_get_mu, mont_get_q_prime, to_mont
from tessera.models.common import load_curves
from tessera.const import ARB_FIELD

SEED = 42

# An arb_field is not a real curve, so its coefficients are only there to
# give a design something to multiply by
ARB_COEFFS = {"a": "0", "b": "1", "d": "2"}


@lru_cache
def get_field(name):
    """
    The complete field struct: bitwidth, modulus, and the computed constants.
    A named field comes from curves.yaml; arb_field_<w> is a random prime of
    width w, seeded so the same name always gives the same prime.
    """
    if name.startswith(ARB_FIELD):
        w = int(name.rsplit("_", 1)[1])
        sympy_seed(SEED)
        q = randprime(1 << (w - 1), (1 << w) - 1)
        coeffs = ARB_COEFFS
    else:
        curve = load_curves()[name]
        w = curve["bitwidth"]
        q = int(curve["q"], 16)
        coeffs = curve

    struct = {
        "w": w,
        "q":       {"w": w,     "val": f"{q:x}"},
        # A constant multiplier bakes one of these in
        "q_prime": {"w": w,     "val": f"{mont_get_q_prime(q):x}"},
        "mu":      {"w": w + 1, "val": f"{barrett_get_mu(q):x}"},
    }

    # The curve's own constants, plain and in the montgomery domain
    for coeff in ("a", "b", "d"):
        if coeff in coeffs:
            value = int(coeffs[coeff], 16) % q
            struct[coeff] = {"w": w, "val": f"{value:x}"}
            struct[f"{coeff}_mont"] = {"w": w, "val": f"{to_mont(value, q):x}"}

    # The twisted edwards addition reads 2d, so it is precomputed
    if "d" in coeffs:
        k = (2 * int(coeffs["d"], 16)) % q
        struct["k"] = {"w": w, "val": f"{k:x}"}
        struct["k_mont"] = {"w": w, "val": f"{to_mont(k, q):x}"}

    return struct
