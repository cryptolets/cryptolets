#include "point_add_te.h"

// Define modmul_core type (rn just montgomery)
wide_t modmul_core(const wide_t x, const wide_t y, const wide_t q, const wide_t q_prime) {
#if MODMUL_TYPE == MODMUL_TYPE_MONT
    return modmul_mont_core(x, y, q, q_prime);
#endif
}

// Twisted Edwards Curve with Extended coordinates

EC_point_EP point_add_te(
    EC_point_EP P0, EC_point_EP P1
#if Q_TYPE == VAR_Q
    , const wide_t q, const wide_t q_prime
#if (FIELD_A == ANEG1)
    , const wide_t field_k
#endif
#if (FIELD_A == AVAR)
    , const wide_t field_a, const wide_t field_d
#endif
#endif
) {

#if Q_TYPE == FIXED_Q
    wide_t q = Q;
    wide_t q_prime = Q_PRIME;

#if (FIELD_A == ANEG1)
    wide_t field_k = FIELD_K_MONT;
#endif

#if (FIELD_A == AVAR)
    wide_t field_a = FIELD_A_MONT;
    wide_t field_d = FIELD_D_MONT;
#endif
#endif

    EC_point_EP result;

#if FIELD_A == ANEG1 // a = -1
    // https://hyperelliptic.org/EFD/g1p/auto-twisted-extended-1.html#addition-add-2008-hwcd-3
    wide_t t0 = modsub_core(P0.Y, P0.X, q)             ; // t0 = Y1-X1
    wide_t t1 = modsub_core(P1.Y, P1.X, q)             ; // t1 = Y2-X2
    wide_t A  = modmul_core(t0, t1, q, q_prime)        ; // A = t0*t1
    wide_t t2 = modadd_core(P0.Y, P0.X, q)             ; // t2 = Y1+X1
    wide_t t3 = modadd_core(P1.Y, P1.X, q)             ; // t3 = Y2+X2
    wide_t B  = modmul_core(t2, t3, q, q_prime)        ; // B = t2*t3
#if Q_TYPE == FIXED_Q
    wide_t t4 = modmul_mont_const(field_k, P1.T, q, q_prime) ; // t4 = k*T2 (const)
#else
    wide_t t4 = modmul_core(field_k, P1.T, q, q_prime) ; // t4 = k*T2 (const)
#endif
    wide_t C  = modmul_core(P0.T, t4, q, q_prime)      ; // C = T1*t4
    wide_t t5 = moddouble_core(P1.Z, q)                     ; // t5 = 2*Z2
    wide_t D  = modmul_core(P0.Z, t5, q, q_prime)      ; // D = Z1*t5
    wide_t E  = modsub_core(B, A, q)                   ; // E = B-A
    wide_t F  = modsub_core(D, C, q)                   ; // F = D-C
    wide_t G  = modadd_core(D, C, q)                   ; // G = D+C
    wide_t H  = modadd_core(B, A, q)                   ; // H = B+A
    result.X  = modmul_core(E, F, q, q_prime)          ; // X3 = E*F
    result.Y  = modmul_core(G, H, q, q_prime)          ; // Y3 = G*H
    result.T  = modmul_core(E, H, q, q_prime)          ; // T3 = E*H
    result.Z  = modmul_core(F, G, q, q_prime)          ; // Z3 = F*G
#else // variable a
    // https://hyperelliptic.org/EFD/g1p/auto-twisted-extended.html#addition-add-2008-hwcd
    wide_t A  = modmul_core(P0.X, P1.X, q, q_prime)      ; // A = X1*X2
    wide_t B  = modmul_core(P0.Y, P1.Y, q, q_prime)      ; // B = Y1*Y2
#if Q_TYPE == FIXED_Q
    wide_t t0 = modmul_mont_const(field_d, P1.T, q, q_prime)   ; // t0 = d*T2 (const)
#else
    wide_t t0 = modmul_core(field_d, P1.T, q, q_prime)   ; // t0 = d*T2 (const)
#endif
    wide_t C  = modmul_core(P0.T, t0, q, q_prime)        ; // C = T1*t0
    wide_t D  = modmul_core(P0.Z, P1.Z, q, q_prime)      ; // D = Z1*Z2
    wide_t t1 = modadd_core(P0.X, P0.Y, q)               ; // t1 = X1+Y1
    wide_t t2 = modadd_core(P1.X, P1.Y, q)               ; // t2 = X2+Y2
    wide_t t3 = modmul_core(t1, t2, q, q_prime)          ; // t3 = t1*t2
    wide_t t4 = modsub_core(t3, A, q)                    ; // t4 = t3-A
    wide_t E  = modsub_core(t4, B, q)                    ; // E = t4-B
    wide_t F  = modsub_core(D, C, q)                     ; // F = D-C
    wide_t G  = modadd_core(D, C, q)                     ; // G = D+C
#if FIELD_A == AVAR
    wide_t t5 = modmul_mont_const(field_a, A, q, q_prime)      ; // t5 = a*A (const)
#else
    wide_t t5 = modmul_core(field_a, A, q, q_prime)      ; // t5 = a*A (const)
#endif
    wide_t H  = modsub_core(B, t5, q)                    ; // H = B-t5
    result.X  = modmul_core(E, F, q, q_prime)            ; // X3 = E*F
    result.Y  = modmul_core(G, H, q, q_prime)            ; // Y3 = G*H
    result.T  = modmul_core(E, H, q, q_prime)            ; // T3 = E*H
    result.Z  = modmul_core(F, G, q, q_prime)            ; // Z3 = F*G
#endif

    return result;
}
