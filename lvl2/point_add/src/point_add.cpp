#include "point_add.h"

// Short Weierstrass Curve

EC_point_J point_add_core(
    EC_point_J P0, 
    EC_point_J P1,
    const wide_t q, const wide_t q_prime
) {
    EC_point_J result;

    if (P0.Z == 0 && P1.Z == 0)
        result = P0;
    else if (P0.Z == 0)
        result = P1;
    else if (P1.Z == 0)
        result = P0;
    else {
        // this converts the jacobian coordinates into affine
        // because 2 different jacobian coordinates could
        // map to the same affine coordinate
        wide_t Z1Z1 = modsq_mont_core(P0.Z, q, q_prime);
        wide_t Z2Z2 = modsq_mont_core(P1.Z, q, q_prime);
        wide_t U1 = modmul_mont_core(P0.X, Z2Z2, q, q_prime);
        wide_t U2 = modmul_mont_core(P1.X, Z1Z1, q, q_prime);
        wide_t Z1_cubed = modmul_mont_core(P0.Z, Z1Z1, q, q_prime);
        wide_t Z2_cubed = modmul_mont_core(P1.Z, Z2Z2, q, q_prime);
        wide_t S1 = modmul_mont_core(P0.Y, Z2_cubed, q, q_prime);
        wide_t S2 = modmul_mont_core(P1.Y, Z1_cubed, q, q_prime);

        // if equal, run the doubling algorithm
        if (U1 == U2 && S1 == S2) {
            wide_t A = modsq_mont_core(P0.X, q, q_prime);
            wide_t B = modsq_mont_core(P0.Y, q, q_prime);
            wide_t C = modsq_mont_core(B, q, q_prime);
            wide_t sum_square = modsq_mont_core(modadd_core(P0.X, B, q), q, q_prime);
            wide_t ss_minus_A = modsub_core(sum_square, A, q);
            wide_t D = modsub_core(ss_minus_A, C, q);
            D = moddouble_core(D, q);
            wide_t E = modadd_core(moddouble_core(A, q), A, q);
            wide_t F = modsq_mont_core(E, q, q_prime);
            wide_t X3 = modsub_core(F, moddouble_core(D, q), q);
            wide_t eightC = moddouble_core(C, q);
            eightC = moddouble_core(eightC, q);
            eightC = moddouble_core(eightC, q);
            wide_t D_sub_X3 = modsub_core(D, X3, q);
            wide_t Y3 = modsub_core(modmul_mont_core(E, D_sub_X3, q, q_prime), eightC, q);
            wide_t Y1Z1 = modmul_mont_core(P0.Y, P0.Z, q, q_prime);
            wide_t Z3 = moddouble_core(Y1Z1, q);
            result.X = X3;
            result.Y = Y3;
            result.Z = Z3;
        } else {
            // otherwise do the addition
            wide_t H = modsub_core(U2, U1, q);
            wide_t S2_minus_S1 = modsub_core(S2, S1, q);
            wide_t I = modsq_mont_core(moddouble_core(H, q), q, q_prime);
            wide_t J = modmul_mont_core(H, I, q, q_prime);
            wide_t r = moddouble_core(S2_minus_S1, q);
            wide_t V = modmul_mont_core(U1, I, q, q_prime);
            wide_t r_squared = modsq_mont_core(r, q, q_prime);
            wide_t r_sq_minus_J = modsub_core(r_squared, J, q);
            wide_t X3 = modsub_core(r_sq_minus_J, moddouble_core(V, q), q);
            wide_t S1_J = modmul_mont_core(S1, J, q, q_prime);
            wide_t V_minus_X3 = modsub_core(V, X3, q);
            wide_t times_r = modmul_mont_core(V_minus_X3, r, q, q_prime);
            wide_t S1_J_double = moddouble_core(S1_J, q);
            wide_t Y3 = modsub_core(times_r, S1_J_double, q);
            wide_t step1 = modadd_core(P0.Z, P1.Z, q);
            wide_t step2 = modsq_mont_core(step1, q, q_prime);
            wide_t step3 = modsub_core(modsub_core(step2, Z1Z1, q), Z2Z2, q);
            wide_t Z3 = modmul_mont_core(step3, H, q, q_prime);
            result.X = X3;
            result.Y = Y3;
            result.Z = Z3;
        }
    }
    return result;
}

#if Q_TYPE == FIXED_Q

EC_point_J point_add(EC_point_J P0, EC_point_J P1) {
    return point_add_core(P0, P1, Q, Q_PRIME);
}

#else  // VARIABLE Q

EC_point_J point_add(
    EC_point_J P0, EC_point_J P1, 
    const wide_t q, const wide_t q_prime
) {
    return point_add_core(P0, P1, q, q_prime);
}

#endif
