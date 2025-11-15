#!/usr/bin/env python3
import argparse
import csv
import random
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.field_helpers import \
    get_field_const, to_mont, from_mont, get_q_prime

def modmul_mont_ref(a, b, q, R, mul_sq=False):
    if mul_sq:
        return (a * a * R) % q
    else:
        return (a * b * R) % q

def generate_samples(bitwidth, total_samples, curve_type, json_file, seed=42):
    q = get_field_const(curve_type, "q", json_file)
    q_prime = get_q_prime(q, bitwidth)
    
    max_val = ((1 << bitwidth) - 1) % q
    mid_val = (max_val // 2) % q

    # Edge cases
    samples = [
        (0, 0, q, q_prime),
        (max_val, max_val, q, q_prime),
        (0, max_val, q, q_prime),
        (max_val, 0, q, q_prime),
        (mid_val, mid_val, q, q_prime)
    ]

    # Remaining random samples, distributed across sub-bitwidth ranges
    num_random = max(total_samples - len(samples), 0)
    if num_random > 0:
        random.seed(seed)
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(num_random):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            sub_max = (1 << sub_bw) - 1
            a = random.randint(0, sub_max) % q
            b = random.randint(0, sub_max) % q
            samples.append((a, b, q, q_prime))

    return samples

def write_csv_files(samples, bitwidth, samples_path=None, golden_path=None, mul_sq=False):
    R = pow(2, bitwidth)

    samples_mont = []
    for a, b, q, q_prime in samples:
        a_mont = to_mont(a, q)
        b_mont = to_mont(b, q)
        samples_mont.append((a_mont, b_mont, q, q_prime))

    # default paths
    samples_file = Path(samples_path) if samples_path else Path("samples") / f"samples_{bitwidth}.csv"
    golden_file  = Path(golden_path)  if golden_path  else Path("goldens") / f"golden_{bitwidth}.csv"

    # make sure dirs exist
    samples_file.parent.mkdir(parents=True, exist_ok=True)
    golden_file.parent.mkdir(parents=True, exist_ok=True)

    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["a_sample", "b_sample", "q_sample", "q_prime_sample"])
        writer.writerows(samples_mont)

    with golden_file.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["o_sample"])
        for a, b, q, q_prime in samples:
            writer.writerow([modmul_mont_ref(a, b, q, R, mul_sq)])

    print(f"Generated {samples_file} and {golden_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for given bitwidth and curve.")
    parser.add_argument("--bw", type=int, required=True, help="Bitwidth of inputs.")
    parser.add_argument("--n", type=int, default=10, help="Total number of samples (including edge cases).")
    parser.add_argument("--curve_type", type=str, default="RAND_CURVE",
                        help="Curve type (e.g., BN128, SECP256K1, BLS12_381).")
    parser.add_argument("--samples-file", type=str, help="Optional path for samples CSV file.")
    parser.add_argument("--golden-file", type=str, help="Optional path for golden CSV file.")
    parser.add_argument("--json-file", type=str, help="json file to get field constant from.")
    parser.add_argument("--mul-sq", action="store_true", default=False, help="Generate square samples.")
    args = parser.parse_args()

    samples = generate_samples(args.bw, args.n, args.curve_type, args.json_file)
    write_csv_files(samples, args.bw, args.samples_file, args.golden_file, args.mul_sq)


