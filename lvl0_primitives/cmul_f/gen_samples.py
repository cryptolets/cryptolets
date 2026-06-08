#!/usr/bin/env python3
import argparse
import csv
import random
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.field_helpers import \
    get_field_const, get_q_prime, get_mu

def cmul_f_ref(a, bitwidth, q_prime):
    return (a * q_prime) & (pow(2,bitwidth)-1)

def generate_samples(bitwidth, total_samples, seed=42):
    max_val = (1 << bitwidth) - 1
    mid_val = max_val // 2

    # Edge cases
    samples = [
        (0),
        (max_val),
        (mid_val)
    ]

    # Remaining random samples, distributed across sub-bitwidth ranges
    num_random = max(total_samples - len(samples), 0)
    if num_random > 0:
        random.seed(seed)
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(num_random):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            sub_max = (1 << sub_bw) - 1
            a = random.randint(0, sub_max)
            samples.append(a)

    return samples

def write_csv_files(samples, bitwidth, curve_type, json_file, samples_path=None, golden_path=None):
    # default paths
    samples_file = Path(samples_path) if samples_path else Path("samples") / f"samples_{bitwidth}.csv"
    golden_file  = Path(golden_path)  if golden_path  else Path("goldens") / f"golden_{bitwidth}.csv"

    # make sure dirs exist
    samples_file.parent.mkdir(parents=True, exist_ok=True)
    golden_file.parent.mkdir(parents=True, exist_ok=True)

    q = get_field_const(curve_type, "q", json_file)
    q_prime = get_q_prime(q, bitwidth)

    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["a_sample"])
        for a in samples:
            writer.writerow([a])

    with golden_file.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["o_sample"])
        for a in samples:
            writer.writerow([cmul_f_ref(a, bitwidth, q_prime)])

    print(f"Generated {samples_file} and {golden_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for given bitwidth.")
    parser.add_argument("--bw", type=int, required=True, help="Bitwidth of inputs.")
    parser.add_argument("--n", type=int, default=10, help="Total number of samples (including edge cases).")
    parser.add_argument("--curve_type", type=str, default="RAND_CURVE", help="Curve type") # this is always RAND_CURVE for cmul_f
    parser.add_argument("--samples-file", type=str, help="Optional path for samples CSV file.")
    parser.add_argument("--golden-file", type=str, help="Optional path for golden CSV file.")
    parser.add_argument("--json-file", type=str, help="json file to get field constant from.")
    args = parser.parse_args()

    samples = generate_samples(args.bw, args.n)
    write_csv_files(samples, args.bw, args.curve_type, args.json_file, args.samples_file, args.golden_file)