#!/usr/bin/env python3
import argparse
import json
import os
import random
from math import gcd
from sympy import randprime, mod_inverse, Integer

FIELD_JSON = "field_const.json"
FIELD_A_TO_INT = {
    "A0": 0,
    "A2": 2,
    "ANEG3": -3,
    "AVAR": 5, # just for testing variable a
    "ANEG1": -1
}

def gen_random_field_const(bitwidth, field_a, seed=42):
    low  = Integer(2) ** (bitwidth - 1)
    high = Integer(2) ** bitwidth - 1
    random.seed(seed + bitwidth)

    q = randprime(low, high)
    R = Integer(1) << bitwidth
    assert gcd(q, R) == 1, "q and R must be coprime"

    q_prime = (-mod_inverse(q, R)) % R
    mu = (Integer(1) << (2 * bitwidth)) // q 

    # --- fixed a ---
    a = FIELD_A_TO_INT[field_a] % q
    a_mont = (a * R) % q

    # --- fixed b=1 ---
    b = 1 % q

    # --- fixed d=2 ---
    d = 2 % q
    d_mont = (d * R) % q
    k = (2 * d) % q
    k_mont = (k * R) % q

    return {
        "a": str(hex(a))[2:],
        "a_mont": str(hex(a_mont))[2:],
        "d": str(hex(d))[2:],
        "d_mont": str(hex(d_mont))[2:],
        "k": str(hex(k))[2:],
        "k_mont": str(hex(k_mont))[2:],
        "b": str(hex(b))[2:],
        "q": str(hex(q))[2:],
        "q_prime": str(hex(q_prime))[2:], 
        "mu": str(hex(mu))[2:],
        "bitwidth": bitwidth
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bitwidth", type=int, required=True, help="bitwidth")
    parser.add_argument("--json-file", type=str, required=True, help="Path to field_const.json file")
    parser.add_argument("--field-a", type=str, default="A0", help="Curve parameter a")

    args = parser.parse_args()
    consts = gen_random_field_const(args.bitwidth, args.field_a)

    with open(args.json_file, "w") as f:
        json.dump({"RAND_CURVE": consts}, f, indent=2)

    print(f"Updated {args.json_file} with {args.bitwidth} constants and field-a={args.field_a}")

if __name__ == "__main__":
    main()