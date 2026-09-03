"""
Build the struct for a generated constant with a given hamming weight.
"""
import random
from functools import lru_cache

SEED = 42


@lru_cache
def gen_hamming_const(w, frac):
    """
    A w-bit constant with round(frac * w) bits set.
    Seeded, so the same (w, frac) always gives the same value.
    """
    ones = round(frac * w)
    assert 0 < ones <= w, f"hamming fraction {frac} sets {ones} of {w} bits"

    # Top bit always set, so the constant is w bits wide
    rng = random.Random((SEED, w, frac))
    bits = [w - 1] + rng.sample(range(w - 1), ones - 1)

    value = 0
    for bit in bits:
        value |= 1 << bit
    return {"w": w, "val": f"{value:x}"}
