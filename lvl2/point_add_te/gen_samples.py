#!/usr/bin/env python3
import argparse
import csv
import random
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.field_helpers import (
    modadd, modsub, modmul, modsq, moddouble,
    EC_point_EP, TwistedEdwards,
    get_field_const, to_mont, from_mont,
    get_q_prime, get_mu
)

random.seed(42)

def point_add_te_ref(P0, P1, q, a, d, k):
    result = EC_point_EP()

    if a == (-1 % q):
        t0       = modsub(P0.Y, P0.X, q) # t0 = Y1-X1
        t1       = modsub(P1.Y, P1.X, q) # t1 = Y2-X2
        A        = modmul(t0, t1, q)     # A = t0*t1
        t2       = modadd(P0.Y, P0.X, q) # t2 = Y1+X1
        t3       = modadd(P1.Y, P1.X, q) # t3 = Y2+X2
        B        = modmul(t2, t3, q)     # B = t2*t3
        t4       = modmul(k, P1.T, q)    # t4 = k*T2
        C        = modmul(P0.T, t4, q)   # C = T1*t4
        t5       = moddouble(P1.Z, q)    # t5 = 2*Z2
        D        = modmul(P0.Z, t5, q)   # D = Z1*t5
        E        = modsub(B, A, q)       # E = B-A
        F        = modsub(D, C, q)       # F = D-C
        G        = modadd(D, C, q)       # G = D+C
        H        = modadd(B, A, q)       # H = B+A
        result.X = modmul(E, F, q)       # X3 = E*F
        result.Y = modmul(G, H, q)       # Y3 = G*H
        result.T = modmul(E, H, q)       # T3 = E*H
        result.Z = modmul(F, G, q)       # Z3 = F*G
    else:
        A        = modmul(P0.X, P1.X, q) # A = X1*X2
        B        = modmul(P0.Y, P1.Y, q) # B = Y1*Y2
        t0       = modmul(d, P1.T, q)    # t0 = d*T2
        C        = modmul(P0.T, t0, q)   # C = T1*t0
        D        = modmul(P0.Z, P1.Z, q) # D = Z1*Z2
        t1       = modadd(P0.X, P0.Y, q) # t1 = X1+Y1
        t2       = modadd(P1.X, P1.Y, q) # t2 = X2+Y2
        t3       = modmul(t1, t2, q)     # t3 = t1*t2
        t4       = modsub(t3, A, q)      # t4 = t3-A
        E        = modsub(t4, B, q)      # E = t4-B
        F        = modsub(D, C, q)       # F = D-C
        G        = modadd(D, C, q)       # G = D+C
        t5       = modmul(a, A, q)       # t5 = a*A
        H        = modsub(B, t5, q)      # H = B-t5
        result.X = modmul(E, F, q)       # X3 = E*F
        result.Y = modmul(G, H, q)       # Y3 = G*H
        result.T = modmul(E, H, q)       # T3 = E*H
        result.Z = modmul(F, G, q)       # Z3 = F*G
    return result


def write_csv_files(
    curve_type, total_samples, json_file, 
    samples_path=None, golden_path=None, 
    is_modmul_mont=True
):
    q = get_field_const(curve_type, "q", json_file)
    bitwidth = get_field_const(curve_type, "bitwidth", json_file)
    q_prime = get_q_prime(q, bitwidth)
    mu = get_mu(q, bitwidth)

    a = get_field_const(curve_type, "a", json_file)
    d = get_field_const(curve_type, "d", json_file)
    k = get_field_const(curve_type, "k", json_file)
    E = TwistedEdwards(q, a=a, d=d)

    # default paths
    samples_file = Path(samples_path) if samples_path else Path("samples") / f"samples_{bitwidth}.csv"
    golden_file  = Path(golden_path)  if golden_path  else Path("goldens") / f"golden_{bitwidth}.csv"

    # make sure dirs exist
    samples_file.parent.mkdir(parents=True, exist_ok=True)
    golden_file.parent.mkdir(parents=True, exist_ok=True)

    samples = []
    goldens = []

    for i in range(total_samples):
        if i < total_samples // 2:
            # Case 1: P1 == P2 (doubling test)
            P1 = E.random_point()
            P2 = P1
        else:
            # Case 2: P1 != P2 (addition test)
            while True:
                P1 = E.random_point()
                P2 = E.random_point()
                if P1 != P2:   # ensure distinct
                    break

        P1_ep = E.aff_to_ep(P1)
        P2_ep = E.aff_to_ep(P2)

        # Convert whole tuples to Montgomery
        if is_modmul_mont:
            P1_mont = to_mont(P1_ep.as_tuple(), q)
            P2_mont = to_mont(P2_ep.as_tuple(), q)

            samples.append((
                *P1_mont, *P2_mont, q, q_prime, 
                to_mont(a,q), to_mont(d,q), to_mont(k,q)
            ))
        else:
            samples.append((
                *P1_ep.as_tuple(), *P2_ep.as_tuple(), q, mu, 
                a, d, k
            ))

        golden_ep = point_add_te_ref(P1_ep, P2_ep, q, a, d, k)
        ref_aff = E.add(P1, P2) # use affine point add for reference (sanity check)
        golden_aff = E.ep_to_aff(golden_ep)
        assert (ref_aff.x, ref_aff.y) == (golden_aff.x, golden_aff.y)

        # another sanity check, to see if all points are on curve
        assert E.is_on_curve(P1) and E.is_on_curve(P2) and E.is_on_curve(golden_aff)

        if is_modmul_mont:
            golden_ep_mont = to_mont(golden_ep.as_tuple(), q)
            goldens.append(golden_ep_mont)
        else:
            goldens.append(golden_ep.as_tuple())

    # Write samples
    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        
        redc_header_name = "q_prime_sample" if is_modmul_mont else "mu_sample"
        samples_header = [
            "X1", "Y1", "Z1", "T1", 
            "X2", "Y2", "Z2", "T2", 
            "q_sample", redc_header_name, 
            "field_a_sample", "field_d_sample", "field_k_sample"
        ]
        writer.writerow(samples_header)
        writer.writerows(samples)

    # Write goldens
    with golden_file.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["X3", "Y3", "Z3", "T3"])
        writer.writerows(goldens)

    print(f"Generated {samples_file} and {golden_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for given curve/bitwidth.")
    parser.add_argument("--bw", type=int, required=True, help="Bitwidth of inputs.")  # still present if needed
    parser.add_argument("--n", type=int, default=10, help="Total number of samples.")
    parser.add_argument("--curve_type", type=str, default="RAND_CURVE", help="Curve type (e.g., BN128, SECP256K1, BLS12_381).")
    parser.add_argument("--samples-file", type=str, help="Optional path for samples CSV file.")
    parser.add_argument("--golden-file", type=str, help="Optional path for golden CSV file.")
    parser.add_argument("--json-file", type=str, help="json file to get field constant from.")
    parser.add_argument("--modmul-type", type=str, help="type of modmul (MODMUL_TYPE_MONT, MODMUL_TYPE_BARRETT)")
    args = parser.parse_args()

    is_modmul_mont = args.modmul_type == "MODMUL_TYPE_MONT"
    write_csv_files(args.curve_type, args.n, args.json_file, args.samples_file, args.golden_file, is_modmul_mont)