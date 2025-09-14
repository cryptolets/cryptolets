#!/usr/bin/env python3
import argparse
import csv
import random
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.field_helpers import get_field_const

def modadd_ref(a, b, q):
    return (a + b) % q

def generate_samples(bitwidth, total_samples, curve_type, seed=42):
    q = get_field_const(curve_type, "q")
    
    max_val = ((1 << bitwidth) - 1) % q
    mid_val = (max_val // 2) % q

    # Edge cases
    samples = [
        (0, 0, q),
        (max_val, max_val, q),
        (0, max_val, q),
        (max_val, 0, q),
        (mid_val, mid_val, q)
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
            samples.append((a, b, q))

    return samples

def write_csv_files(samples, bitwidth):
    samples_dir = Path("samples")
    goldens_dir = Path("goldens")
    samples_dir.mkdir(exist_ok=True)
    goldens_dir.mkdir(exist_ok=True)

    samples_file = samples_dir / f"samples_{bitwidth}.csv"
    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["a_sample", "b_sample", "q_sample"])
        writer.writerows(samples)

    golden_file = goldens_dir / f"golden_{bitwidth}.csv"
    with golden_file.open("w", newline=os.linesep) as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["o_sample"])
        for a, b, q in samples:
            writer.writerow([modadd_ref(a, b, q)])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for given bitwidth.")
    parser.add_argument("--bw", type=int, required=True, help="Bitwidth of inputs.")
    parser.add_argument("--n", type=int, default=10, help="Total number of samples (including edge cases).")
    parser.add_argument("--curve_type", type=str, default="RAND_CURVE", required=True, help="Curve type (e.g., BN128, SECP256K1, BLS12_381).")
    args = parser.parse_args()

    samples = generate_samples(args.bw, args.n, args.curve_type)
    write_csv_files(samples, args.bw)
    print(f"Generated samples/samples_{args.bw}.csv and goldens/golden_{args.bw}.csv")
