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
    EC_point_J, ShortWeierstrass,
    get_field_const, to_mont, from_mont
)

random.seed(42)

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
        Z1Z1     = modsq(P0.Z, q)         # Z1Z1 = Z1^2
        Z2Z2     = modsq(P1.Z, q)         # Z2Z2 = Z2^2
        U1       = modmul(P0.X, Z2Z2, q)  # U1 = X1*Z2Z2
        U2       = modmul(P1.X, Z1Z1, q)  # U2 = X2*Z1Z1
        t0       = modmul(P1.Z, Z2Z2, q)  # t0 = Z2*Z2Z2
        S1       = modmul(P0.Y, t0, q)    # S1 = Y1*t0
        t1       = modmul(P0.Z, Z1Z1, q)  # t1 = Z1*Z1Z1
        S2       = modmul(P1.Y, t1, q)    # S2 = Y2*t1

        # if equal, run the doubling algorithm
        if U1 == U2 and S1 == S2:
            # https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-0.html#doubling-dbl-2009-l
            A        = modsq(P0.X, q)         # A = X1^2
            B        = modsq(P0.Y, q)         # B = Y1^2
            C        = modsq(B, q)            # C = B^2
            t0       = modadd(P0.X, B, q)     # t0 = X1+B
            t1       = modsq(t0, q)           # t1 = t0^2
            t2       = modsub(t1, A, q)       # t2 = t1-A
            t3       = modsub(t2, C, q)       # t3 = t2-C
            D        = moddouble(t3, q)       # D = 2*t3
            E        = moddouble(A, q)        # E = A+A
            E        = modadd(E, A, q)        # E = E+A
            F        = modsq(E, q)            # F = E^2
            t4       = moddouble(D, q)        # t4 = 2*D
            result.X = modsub(F, t4, q)       # X3 = F-t4
            t5       = modsub(D, result.X, q) # t5 = D-X3
            t6       = moddouble(C, q)        # t6 = C+C
            t6       = moddouble(t6, q)       # t6 = t6+t6
            t6       = moddouble(t6, q)       # t6 = t6+t6
            t7       = modmul(E, t5, q)       # t7 = E*t5
            result.Y = modsub(t7, t6, q)      # Y3 = t7-t6
            t8       = modmul(P0.Y, P0.Z, q)  # t8 = Y1*Z1
            result.Z = moddouble(t8, q)       # Z3 = 2*t8
        # otherwise do the addition
        else:
            H        = modsub(U2, U1, q)      # H = U2-U1
            t2       = moddouble(H, q)        # t2 = 2*H
            I        = modsq(t2, q)           # I = t2^2
            J        = modmul(H, I, q)        # J = H*I
            t3       = modsub(S2, S1, q)      # t3 = S2-S1
            r        = moddouble(t3, q)       # r = 2*t3
            V        = modmul(U1, I, q)       # V = U1*I
            t4       = modsq(r, q)            # t4 = r^2
            t5       = moddouble(V, q)        # t5 = 2*V
            t6       = modsub(t4, J, q)       # t6 = t4-J
            result.X = modsub(t6, t5, q)      # X3 = t6-t5
            t7       = modsub(V, result.X, q) # t7 = V-X3
            t8       = modmul(S1, J, q)       # t8 = S1*J
            t9       = moddouble(t8, q)       # t9 = 2*t8
            t10      = modmul(r, t7, q)       # t10 = r*t7
            result.Y = modsub(t10, t9, q)     # Y3 = t10-t9
            t11      = modadd(P0.Z, P1.Z, q)  # t11 = Z1+Z2
            t12      = modsq(t11, q)          # t12 = t11^2
            t13      = modsub(t12, Z1Z1, q)   # t13 = t12-Z1Z1
            t14      = modsub(t13, Z2Z2, q)   # t14 = t13-Z2Z2
            result.Z = modmul(t14, H, q)      # Z3 = t14*H

    return result


def write_csv_files(curve_type, total_samples, json_file, samples_path=None, golden_path=None):
    q = get_field_const(curve_type, "q", json_file)
    q_prime = get_field_const(curve_type, "q_prime", json_file)
    bitwidth = get_field_const(curve_type, "bitwidth", json_file)
    a = get_field_const(curve_type, "a", json_file)
    b = get_field_const(curve_type, "b", json_file)
    
    if a != 0 and curve_type == "RAND_CURVE":
        print(f"Warning: overriding a={a} to a=0")
        a = 0

    assert a == 0, f"Error: a={a}, must be a=0 for this formula"
    E = ShortWeierstrass(q, a=a, b=b)

    # default paths
    samples_file = Path(samples_path) if samples_path else Path("samples") / f"samples_{bitwidth}.csv"
    golden_file  = Path(golden_path)  if golden_path  else Path("goldens") / f"golden_{bitwidth}.csv"

    # make sure dirs exist
    samples_file.parent.mkdir(parents=True, exist_ok=True)
    golden_file.parent.mkdir(parents=True, exist_ok=True)

    samples_mont = []
    goldens_mont = []

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

        P1_jac = E.aff_to_jac(P1)
        P2_jac = E.aff_to_jac(P2)

        # Convert whole tuples to Montgomery
        P1_mont = to_mont(P1_jac.as_tuple(), q)
        P2_mont = to_mont(P2_jac.as_tuple(), q)

        samples_mont.append((*P1_mont, *P2_mont, q, q_prime))

        golden_jac = point_add_ref(P1_jac, P2_jac, q)
        ref_aff = E.add(P1, P2) # use affine point add for reference (sanity check)
        golden_aff = E.jac_to_aff(golden_jac)
        assert (ref_aff.x, ref_aff.y) == (golden_aff.x, golden_aff.y)

        # another sanity check, to see if all points are on curve
        assert E.is_on_curve(P1) and E.is_on_curve(P2) and E.is_on_curve(golden_aff)

        golden_jac_mont = to_mont(golden_jac.as_tuple(), q)
        goldens_mont.append(golden_jac_mont)

    # Write samples
    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["X1", "Y1", "Z1", "X2", "Y2", "Z2", "q_sample", "q_prime_sample"])
        writer.writerows(samples_mont)

    # Write goldens
    with golden_file.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["X3", "Y3", "Z3"])
        writer.writerows(goldens_mont)

    print(f"Generated {samples_file} and {golden_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for given curve/bitwidth.")
    parser.add_argument("--bw", type=int, required=True, help="Bitwidth of inputs.")  # still present if needed
    parser.add_argument("--n", type=int, default=10, help="Total number of samples.")
    parser.add_argument("--curve_type", type=str, default="RAND_CURVE", help="Curve type (e.g., BN128, SECP256K1, BLS12_381).")
    parser.add_argument("--samples-file", type=str, help="Optional path for samples CSV file.")
    parser.add_argument("--golden-file", type=str, help="Optional path for golden CSV file.")
    parser.add_argument("--json-file", type=str, help="json file to get field constant from.")
    args = parser.parse_args()

    write_csv_files(args.curve_type, args.n, args.json_file, args.samples_file, args.golden_file)