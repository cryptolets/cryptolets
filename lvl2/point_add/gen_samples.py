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
    get_field_const, to_mont, from_mont,
    get_q_prime, get_mu
)

random.seed(42)

def point_dbl_2009_l_a_0_ref(P0, q):
    # point doubling for a=0
    # https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-0.html#doubling-dbl-2009-l
    result = EC_point_J()
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
    return result

def point_dbl_2009_l_a_3_ref(P0, delta, q):
    # point doubling for a=-3
    # https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-3.html#doubling-dbl-2001-b
    result = EC_point_J()
    # delta    = modsq(P0.Z, q)          # delta = Z1^2
    gamma    = modsq(P0.Y, q)          # gamma = Y1^2
    beta     = modmul(P0.X, gamma, q)  # beta = X1*gamma
    t0       = modsub(P0.X, delta, q)  # t0 = X1-delta
    t1       = modadd(P0.X, delta, q)  # t1 = X1+delta
    t2       = modmul(t0, t1, q)       # t2 = t0*t1
    alpha    = moddouble(t2, q)        # alpha = t2+t2
    alpha    = modadd(t2, alpha, q)    # alpha = t2+alpha
    t3       = modsq(alpha, q)         # t3 = alpha^2
    t4       = moddouble(beta, q)      # t4 = beta+beta
    t8       = moddouble(t4, q)        # t8 = t4+t4
    t4       = moddouble(t8, q)        # t4 = t8+t8
    result.X = modsub(t3, t4, q)       # X3 = t3-t4
    t5       = modadd(P0.Y, P0.Z, q)   # t5 = Y1+Z1
    t6       = modsq(t5, q)            # t6 = t5^2
    t7       = modsub(t6, gamma, q)    # t7 = t6-gamma
    result.Z = modsub(t7, delta, q)    # Z3 = t7-delta
    t9       = modsub(t8, result.X, q) # t9 = t8-X3
    t10      = modsq(gamma, q)         # t10 = gamma^2
    t11      = moddouble(t10, q)       # t11 = t10+t10
    t11      = moddouble(t11, q)       # t11 = t11+t11
    t11      = moddouble(t11, q)       # t11 = t11+t11
    t12      = modmul(alpha, t9, q)    # t12 = alpha*t9
    result.Y = modsub(t12, t11, q)     # Y3 = t12-t11
    return result

def point_dbl_2009_l_a_var_ref(P0, q, a):
    # point doubling for variable a
    # Note: this is a general formula, but 2*A mod q translates to A+A mod q, which is easy in hardware
    # https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian.html#doubling-dbl-2007-bl
    result = EC_point_J()
    XX       = modsq(P0.X, q)        # XX = X1^2
    YY       = modsq(P0.Y, q)        # YY = Y1^2
    YYYY     = modsq(YY, q)          # YYYY = YY^2
    ZZ       = modsq(P0.Z, q)        # ZZ = Z1^2
    t0       = modadd(P0.X, YY, q)   # t0 = X1+YY
    t1       = modsq(t0, q)          # t1 = t0^2
    t2       = modsub(t1, XX, q)     # t2 = t1-XX
    t3       = modsub(t2, YYYY, q)   # t3 = t2-YYYY
    S        = moddouble(t3, q)      # S = 2*t3
    t4       = modsq(ZZ, q)          # t4 = ZZ^2

    if a == 2:
        # point doubling for a=2
        t5   = moddouble(t4, q)      # t5 = a*t4; a = 2
    else:
        t5   = modmul(a, t4, q)      # t5 = a*t4

    t6       = moddouble(XX, q)      # t6 = XX+XX
    t6       = modadd(t6, XX, q)     # t6 = t6+XX
    M        = modadd(t6, t5, q)     # M = t6+t5
    t7       = modsq(M, q)           # t7 = M^2
    t8       = moddouble(S, q)       # t8 = 2*S
    T        = modsub(t7, t8, q)     # T = t7-t8
    result.X = T                     # X3 = T
    t9       = modsub(S, T, q)       # t9 = S-T
    t10      = moddouble(YYYY, q)    # t10 = YYYY+YYYY
    t10      = moddouble(t10, q)     # t10 = t10+t10
    t10      = moddouble(t10, q)     # t10 = t10+t10
    t11      = modmul(M, t9, q)      # t11 = M*t9
    result.Y = modsub(t11, t10, q)   # Y3 = t11-t10
    t12      = modadd(P0.Y, P0.Z, q) # t12 = Y1+Z1
    t13      = modsq(t12, q)         # t13 = t12^2
    t14      = modsub(t13, YY, q)    # t14 = t13-YY
    result.Z = modsub(t14, ZZ, q)    # Z3 = t14-ZZ
    return result


def point_add_ref(P0, P1, q, a):
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
            if a == 0:
                result = point_dbl_2009_l_a_0_ref(P0, q)
            elif a == (-3 % q):
                result = point_dbl_2009_l_a_3_ref(P0, Z1Z1, q)
            else:
                result = point_dbl_2009_l_a_var_ref(P0, q, a)

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
    b = get_field_const(curve_type, "b", json_file)
    E = ShortWeierstrass(q, a=a, b=b)

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

        P1_jac = E.aff_to_jac(P1)
        P2_jac = E.aff_to_jac(P2)

        # Convert whole tuples to Montgomery
        if is_modmul_mont:
            P1_mont = to_mont(P1_jac.as_tuple(), q)
            P2_mont = to_mont(P2_jac.as_tuple(), q)

            samples.append((*P1_mont, *P2_mont, q, q_prime, to_mont(a,q)))
        else:
            samples.append((*P1_jac.as_tuple(), *P2_jac.as_tuple(), q, mu, a))

        golden_jac = point_add_ref(P1_jac, P2_jac, q, a)
        ref_aff = E.add(P1, P2) # use affine point add for reference (sanity check)
        golden_aff = E.jac_to_aff(golden_jac)
        assert (ref_aff.x, ref_aff.y) == (golden_aff.x, golden_aff.y)

        # another sanity check, to see if all points are on curve
        assert E.is_on_curve(P1) and E.is_on_curve(P2) and E.is_on_curve(golden_aff)

        if is_modmul_mont:
            golden_jac_mont = to_mont(golden_jac.as_tuple(), q)
            goldens.append(golden_jac_mont)
        else:
            goldens.append(golden_jac.as_tuple())

    # Write samples
    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        redc_header_name = "q_prime_sample" if is_modmul_mont else "mu_sample"
        samples_header = ["X1", "Y1", "Z1", "X2", "Y2", "Z2", "q_sample", redc_header_name, "field_a_sample"]
        writer.writerow(samples_header)
        writer.writerows(samples)

    # Write goldens
    with golden_file.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(["X3", "Y3", "Z3"])
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