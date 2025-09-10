#!/usr/bin/env python3
import argparse
import csv
import random
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils import CONST_Q, CONST_Q_PRIME

# bn128
Q = 0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47
Q_PRIME = 0xf57a22b791888c6bd8afcbd01833da809ede7d651eca6ac987d20782e4866389

class EC_point_J:
    def __init__(self, X=0, Y=0, Z=0):
        self.X = X
        self.Y = Y
        self.Z = Z

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

def point_add_ref(P0, P1, q):
    result = EC_point_J()

    if (P0.Z == 0 and P1.Z == 0):
        result = P0
    elif P0.Z == 0:
        result = P1
    elif P1.Z == 0:
        result = P0
    else:

        # this converts the jacobian coordinates into affine
        # because 2 different jacobian coordinates could
        # map to the same affine coordinate
        Z1Z1 = modsq(P0.Z, q)
        Z2Z2 = modsq(P1.Z, q)
        U1 = modmul(P0.X, Z2Z2, q)
        U2 = modmul(P1.X, Z1Z1, q)
        Z1_cubed = modmul(P0.Z, Z1Z1, q)
        Z2_cubed = modmul(P1.Z, Z2Z2, q)
        S1 = modmul(P0.Y, Z2_cubed, q)
        S2 = modmul(P1.Y, Z1_cubed, q)

        # if equal, run the doubling algorithm
        if U1 == U2 and S1 == S2:
            A = modmul(P0.X, P0.X, q)
            B = modmul(P0.Y, P0.Y, q)
            C = modmul(B, B, q)
            sum_square = modsq(modadd(P0.X, B, q), q)
            ss_minus_A = modsub(sum_square, A, q)
            D = modsub(ss_minus_A, C, q)
            D = modadd(D, D, q)
            E = modadd(modadd(A, A, q), A, q)
            F = modsq(E, q)
            X3 = modsub(F, modadd(D, D, q), q)
            eightC = modadd(C, C, q)
            eightC = modadd(eightC, eightC, q)
            eightC = modadd(eightC, eightC, q)
            D_sub_X3 = modsub(D, X3, q)
            Y3 = modsub(modmul(E, D_sub_X3, q), eightC, q)
            Y1Z1 = modmul(P0.Y, P0.Z, q)
            Z3 = modadd(Y1Z1, Y1Z1, q)
            result.X = X3
            result.Y = Y3
            result.Z = Z3
        # otherwise do the addition
        else:
            H = modsub(U2, U1, q)
            S2_minus_S1 = modsub(S2, S1, q)
            I = modsq(modadd(H, H, q), q)
            J = modmul(H, I, q)
            r = modadd(S2_minus_S1, S2_minus_S1, q)
            V = modmul(U1, I, q)
            r_squared = modsq(r, q)
            r_sq_minus_J = modsub(r_squared, J, q)
            X3 = modsub(r_sq_minus_J, modadd(V, V, q), q)
            S1_J = modmul(S1, J, q)
            V_minus_X3 = modsub(V, X3, q)
            times_r = modmul(V_minus_X3, r, q)
            S1_J_double = modadd(S1_J, S1_J, q)
            Y3 = modsub(times_r, S1_J_double, q)
            step1 = modadd(P0.Z, P1.Z, q)
            step2 = modsq(step1, q)
            step3 = modsub(modsub(step2, Z1Z1, q), Z2Z2, q)
            Z3 = modmul(step3, H, q)
            result.X = X3
            result.Y = Y3
            result.Z = Z3
    return result

def generate_samples(bitwidth, total_samples, seed=42):
    # q = Q
    # q_prime = Q_PRIME
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
            X2 = random.randint(0, sub_max) % q
            Y2 = random.randint(0, sub_max) % q
            Z2 = random.randint(0, sub_max) % q
            samples.append((X1, Y1, Z1, X2, Y2, Z2, q, q_prime))

    return samples

def write_csv_files(samples, bitwidth):
    samples_dir = Path("samples")
    goldens_dir = Path("goldens")
    samples_dir.mkdir(exist_ok=True)
    goldens_dir.mkdir(exist_ok=True)

    R = pow(2, bitwidth)
    samples_mont = []
    
    for X1, Y1, Z1, X2, Y2, Z2, q, q_prime in samples:
        X1_mont = (X1 * R) % q
        Y1_mont = (Y1 * R) % q
        Z1_mont = (Z1 * R) % q
        X2_mont = (X2 * R) % q
        Y2_mont = (Y2 * R) % q
        Z2_mont = (Z2 * R) % q
        samples_mont.append((X1_mont, Y1_mont, Z1_mont, X2_mont, Y2_mont, Z2_mont, q, q_prime))

    samples_file = samples_dir / f"samples_{bitwidth}.csv"
    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["X1", "Y1", "Z1", "X2", "Y2", "Z2", "q_sample", "q_prime_sample"])
        writer.writerows(samples_mont)

    golden_file = goldens_dir / f"golden_{bitwidth}.csv"

    with golden_file.open("w", newline=os.linesep) as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["X3","Y3","Z3"])
        for X1, Y1, Z1, X2, Y2, Z2, q, q_prime in samples:
            P0 = EC_point_J(X1, Y1, Z1)
            P1 = EC_point_J(X2, Y2, Z2)
            res = point_add_ref(P0, P1, q)
            res.X_mont = (res.X * R) % q
            res.Y_mont = (res.Y * R) % q
            res.Z_mont = (res.Z * R) % q
            writer.writerow([res.X_mont, res.Y_mont, res.Z_mont])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for given bitwidth.")
    parser.add_argument("--bw", type=int, required=True, help="Bitwidth of inputs.")
    parser.add_argument("--n", type=int, default=10, help="Total number of samples (including edge cases).")
    args = parser.parse_args()

    samples = generate_samples(args.bw, args.n)
    write_csv_files(samples, args.bw)
    print(f"Generated samples/samples_{args.bw}.csv and goldens/golden_{args.bw}.csv")
