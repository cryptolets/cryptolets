"""
Resolve the field a design works over.

A design names a curve and one of its fields, or arb_curve for a random
prime of the requested bitwidth.
"""
from sympy import randprime
from sympy.core.random import seed as sympy_seed

from tessera.config import ARB_CURVE, curves

SEED = 42
FIELD_CONSTANTS = ("q",) # constant kernel parameters


def get_modulus(design, seed=SEED):
    curve = design.get("curve", ARB_CURVE)
    if curve != ARB_CURVE:
        return int(curves()[curve][design.get("field", "base")]["q"], 16)

    bitwidth = design["bitwidth"]
    sympy_seed(seed)
    return randprime(1 << (bitwidth - 1), (1 << bitwidth) - 1)


def design_fields(design):
    """
    Generated Field (with prime modulus, bitwidth, etc.) descriptors into params.h
    """
    curve = design.get("curve", ARB_CURVE)
    field = design.get("field", "base")
    name = curve if curve == ARB_CURVE else f"{curve}_{field}"

    return [{
        "name": name,
        "bitwidth": design["bitwidth"],
        "q": f"{get_modulus(design):x}",
    }]
