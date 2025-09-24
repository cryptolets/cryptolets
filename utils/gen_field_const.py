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
    "AVAR": 5 # just for testing variable a
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

    return {
        "a": str(hex(FIELD_A_TO_INT[field_a] % q))[2:],
        "b": "1",
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