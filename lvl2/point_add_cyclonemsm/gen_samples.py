#!/usr/bin/env python3
import argparse
import csv
import random
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils import CONST_Q, CONST_Q_PRIME

class EC_point_EP:
    def __init__(self, X=0, Y=0, Z=0, T=0):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.T = T

class EC_point_EA:
    def __init__(self, x=0, y=0, u=0):
        self.x = x
        self.y = y
        self.u = u

def modadd(a, b, q):
    return (a + b) % q

def moddouble(a, q):
    return (a + a) % q

def modsub(a, b, q):
    return (a - b) % q

def modsq(a, q):
    return (a * a) % q

def modmul(a, b, q):
    return (a * b) % q

def point_add_cyclonemsm_ref(P0, P1, q):
    R = EC_point_EP()
    R1  = modsub(P0.Y, P0.X, q) # R1 = Y1-X1
    R2  = modsub(P1.y, P1.x, q) # R2 = y2-x2
    R3  = modadd(P0.Y, P0.X, q) # R3 = Y1+X1
    R4  = modadd(P1.y, P1.x, q) # R4 = y2+x2
    R5  = modadd(R1, R2, q)     # R5 = R1+R2
    R6  = modmul(R3, R4, q)     # R6 = R3*R4
    R7  = modmul(P0.T, P1.u, q) # R7 = T1*u2
    R8  = moddouble(P0.Z, q)    # R8 = 2*Z1
    R9  = modsub(R6, R5, q)     # R9 = R6-R5
    R10 = modsub(R8, R7, q)     # R10 = R8-R7
    R11 = modadd(R8, R7, q)     # R11 = R8+R7
    R12 = modadd(R6, R5, q)     # R12 = R6+R5
    R.X = modmul(R9, R10, q)    # X3 = R9*R10
    R.Y = modmul(R11, R12, q)   # Y3 = R11*R12
    R.Z = modmul(R10, R11, q)   # Z3 = R10*R11
    R.T = modmul(R9, R12, q)    # T3 = R9*R12 
    return R

def generate_samples(bitwidth, total_samples, seed=42):
    q = CONST_Q[bitwidth]
    q_prime = CONST_Q_PRIME[bitwidth]
    samples = []

    # Remaining random samples, distributed across sub-bitwidth ranges
    num_random = max(total_samples - len(samples), 0)
    if num_random > 0:
        random.seed(seed)
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(num_random):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            sub_max = (1 << sub_bw) - 1
            X1 = random.randint(0, sub_max) % q
            Y1 = random.randint(0, sub_max) % q
            Z1 = random.randint(0, sub_max) % q
            T1 = random.randint(0, sub_max) % q

            x2 = random.randint(0, sub_max) % q
            y2 = random.randint(0, sub_max) % q
            u2 = random.randint(0, sub_max) % q
            samples.append((X1, Y1, Z1, T1, x2, y2, u2, q, q_prime))

    return samples

def write_csv_files(samples, bitwidth):
    samples_dir = Path("samples")
    goldens_dir = Path("goldens")
    samples_dir.mkdir(exist_ok=True)
    goldens_dir.mkdir(exist_ok=True)

    R = pow(2, bitwidth)
    samples_mont = []
    
    for X1, Y1, Z1, T1, x2, y2, u2, q, q_prime in samples:
        X1_mont = (X1 * R) % q
        Y1_mont = (Y1 * R) % q
        Z1_mont = (Z1 * R) % q
        T1_mont = (T1 * R) % q
        x2_mont = (x2 * R) % q
        y2_mont = (y2 * R) % q
        u2_mont = (u2 * R) % q
        samples_mont.append((X1_mont, Y1_mont, Z1_mont, T1_mont, x2_mont, y2_mont, u2_mont, q, q_prime))

    samples_file = samples_dir / f"samples_{bitwidth}.csv"
    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["X1", "Y1", "Z1", "T1", "x2", "y2", "u2", "q_sample", "q_prime_sample"])
        writer.writerows(samples_mont)

    golden_file = goldens_dir / f"golden_{bitwidth}.csv"

    with golden_file.open("w", newline=os.linesep) as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["X3","Y3","Z3", "T3"])
        for X1, Y1, Z1, T1, x2, y2, u2, q, q_prime in samples:
            P0 = EC_point_EP(X1, Y1, Z1, T1)
            P1 = EC_point_EA(x2, y2, u2)
            res = point_add_cyclonemsm_ref(P0, P1, q)
            res.X_mont = (res.X * R) % q
            res.Y_mont = (res.Y * R) % q
            res.Z_mont = (res.Z * R) % q
            res.T_mont = (res.T * R) % q
            writer.writerow([res.X_mont, res.Y_mont, res.Z_mont, res.T_mont])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for given bitwidth.")
    parser.add_argument("--bw", type=int, required=True, help="Bitwidth of inputs.")
    parser.add_argument("--n", type=int, default=10, help="Total number of samples (including edge cases).")
    args = parser.parse_args()

    samples = generate_samples(args.bw, args.n)
    write_csv_files(samples, args.bw)
    print(f"Generated samples/samples_{args.bw}.csv and goldens/golden_{args.bw}.csv")
