#!/usr/bin/env python3
import argparse
import json
import os
import random
from math import gcd
from sympy import randprime, Integer
from field_helpers import to_mont
from common import fa_to_int, to_hex

def gen_random_field_const(bitwidth, field_a, seed=42):
    low  = Integer(2) ** (bitwidth - 1)
    high = Integer(2) ** bitwidth - 1
    random.seed(seed + bitwidth)

    q = randprime(low, high)
    R = Integer(1) << bitwidth
    assert gcd(q, R) == 1, "q and R must be coprime"

    a = fa_to_int(field_a) % q
    b = 1 % q # fixed b=1
    d = 2 % q # fixed d=2
    k = (2 * d) % q

    return {
        "a": to_hex(a),
        "b": to_hex(b),
        "d": to_hex(d),
        "k": to_hex(k),
        "q": to_hex(q),
        "bitwidth": bitwidth,
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