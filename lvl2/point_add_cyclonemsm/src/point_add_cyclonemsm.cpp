#include "point_add_cyclonemsm.h"

EC_point_EP point_add_cyclonemsm_core(
    EC_point_EP P0, 
    EC_point_EA P1,
    const wide_t q, const wide_t q_prime
) {
    EC_point_EP R;
    wide_t R1  = modsub_core(P0.Y, P0.X, q)      ; // R1 = Y1-X1
    wide_t R2  = modsub_core(P1.y, P1.x, q)      ; // R2 = y2-x2
    wide_t R3  = modadd_core(P0.Y, P0.X, q)      ; // R3 = Y1+X1
    wide_t R4  = modadd_core(P1.y, P1.x, q)     ; // R4 = y2+x2
    wide_t R5  = modadd_core(R1, R2, q)          ; // R5 = R1+R2
    wide_t R6  = modmul_mont_core(R3, R4, q, q_prime)     ; // R6 = R3*R4
    wide_t R7  = modmul_mont_core(P0.T, P1.u, q, q_prime) ; // R7 = T1*u2
    wide_t R8  = moddouble_core(P0.Z, q)         ; // R8 = 2*Z1
    wide_t R9  = modsub_core(R6, R5, q)          ; // R9 = R6-R5
    wide_t R10 = modsub_core(R8, R7, q)          ; // R10 = R8-R7
    wide_t R11 = modadd_core(R8, R7, q)          ; // R11 = R8+R7
    wide_t R12 = modadd_core(R6, R5, q)          ; // R12 = R6+R5
    R.X        = modmul_mont_core(R9, R10, q, q_prime)    ; // X3 = R9*R10
    R.Y        = modmul_mont_core(R11, R12, q, q_prime)   ; // Y3 = R11*R12
    R.Z        = modmul_mont_core(R10, R11, q, q_prime)   ; // Z3 = R10*R11
    R.T        = modmul_mont_core(R9, R12, q, q_prime)    ; // T3 = R9*R12
    return R;
}

#if Q_TYPE == FIXED_Q

EC_point_EP point_add_cyclonemsm(
    EC_point_EP P0, 
    EC_point_EA P1
) {
    return point_add_cyclonemsm_core(P0, P1, Q, Q_PRIME);
}

#else  // VARIABLE Q

EC_point_EP point_add_cyclonemsm(
    EC_point_EP P0, 
    EC_point_EA P1,
    const wide_t q, const wide_t q_prime
) {
    return point_add_cyclonemsm_core(P0, P1, q, q_prime);
}

#endif
