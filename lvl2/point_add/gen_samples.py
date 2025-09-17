#!/usr/bin/env python3
import argparse
import csv
import random
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.field_helpers import (
    modadd, modsub, modmul, modsq, 
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


def write_csv_files(curve_type, total_samples, samples_path=None, golden_path=None):
    q = get_field_const(curve_type, "q")
    q_prime = get_field_const(curve_type, "q_prime")
    bitwidth = get_field_const(curve_type, "bitwidth")

    E = ShortWeierstrass(q, a=2, b=3)

    # default paths
    samples_file = Path(samples_path) if samples_path else Path("samples") / f"samples_{bitwidth}.csv"
    golden_file  = Path(golden_path)  if golden_path  else Path("goldens") / f"golden_{bitwidth}.csv"

    # make sure dirs exist
    samples_file.parent.mkdir(parents=True, exist_ok=True)
    golden_file.parent.mkdir(parents=True, exist_ok=True)

    samples_mont = []
    goldens_mont = []

    for _ in range(total_samples):
        P1 = E.random_point()
        P2 = E.random_point()

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
    args = parser.parse_args()

    write_csv_files(args.curve_type, args.n, args.samples_file, args.golden_file)