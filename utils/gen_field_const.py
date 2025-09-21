#!/usr/bin/env python3
import argparse
import json
import os
import random
from math import gcd
from sympy import randprime, mod_inverse, Integer

FIELD_JSON = "field_const.json"

def gen_random_field_const(bitwidth, seed=42):
    low  = Integer(2) ** (bitwidth - 1)
    high = Integer(2) ** bitwidth - 1
    random.seed(seed + bitwidth)

    q = randprime(low, high)
    R = Integer(1) << bitwidth
    assert gcd(q, R) == 1, "q and R must be coprime"

    q_prime = (-mod_inverse(q, R)) % R
    mu = (Integer(1) << (2 * bitwidth)) // q
    return {
        "a": "0",
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

    args = parser.parse_args()
    consts = gen_random_field_const(args.bitwidth)

    with open(args.json_file, "w") as f:
        json.dump({"RAND_CURVE": consts}, f, indent=2)

    print(f"Updated {args.json_file} with {args.bitwidth} constants")

if __name__ == "__main__":
    main()