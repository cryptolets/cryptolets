#include "point_add_mnt.h"

// Short Weierstrass Curve (a = 2)
EC_point_J point_add_mnt_core(
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
        wide_t Z1Z1 = modsq_mont_core(P0.Z, q, q_prime)        ; // Z1Z1 = Z1^2
        wide_t Z2Z2 = modsq_mont_core(P1.Z, q, q_prime)        ; // Z2Z2 = Z2^2
        wide_t U1   = modmul_mont_core(P0.X, Z2Z2, q, q_prime) ; // U1 = X1*Z2Z2
        wide_t U2   = modmul_mont_core(P1.X, Z1Z1, q, q_prime) ; // U2 = X2*Z1Z1
        wide_t t0   = modmul_mont_core(P1.Z, Z2Z2, q, q_prime) ; // t0 = Z2*Z2Z2
        wide_t S1   = modmul_mont_core(P0.Y, t0, q, q_prime)   ; // S1 = Y1*t0
        wide_t t1   = modmul_mont_core(P0.Z, Z1Z1, q, q_prime) ; // t1 = Z1*Z1Z1
        wide_t S2   = modmul_mont_core(P1.Y, t1, q, q_prime)   ; // S2 = Y2*t1

        // if equal, run the doubling algorithm
        if (U1 == U2 && S1 == S2) {
            // https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-0.html#doubling-dbl-2009-l
            wide_t XX   = modsq_mont_core(P0.X, q, q_prime)   ; // XX = X1^2
            wide_t YY   = modsq_mont_core(P0.Y, q, q_prime)   ; // YY = Y1^2
            wide_t YYYY = modsq_mont_core(YY, q, q_prime)     ; // YYYY = YY^2
            wide_t ZZ   = modsq_mont_core(P0.Z, q, q_prime)   ; // ZZ = Z1^2
            wide_t t0   = modadd_core(P0.X, YY, q)            ; // t0 = X1+YY
            wide_t t1   = modsq_mont_core(t0, q, q_prime)     ; // t1 = t0^2
            wide_t t2   = modsub_core(t1, XX, q)              ; // t2 = t1-XX
            wide_t t3   = modsub_core(t2, YYYY, q)            ; // t3 = t2-YYYY
            wide_t S    = moddouble_core(t3, q)               ; // S = 2*t3
            wide_t t4   = modsq_mont_core(ZZ, q, q_prime)     ; // t4 = ZZ^2
            wide_t t5   = moddouble_core(t4, q)               ; // t5 = a*t4; a=2
            wide_t t6   = moddouble_core(XX, q)               ; // t6 = XX+XX
            t6          = modadd_core(t6, XX, q)              ; // t6 = t6+XX
            wide_t M    = modadd_core(t6, t5, q)              ; // M = t6+t5
            wide_t t7   = modsq_mont_core(M, q, q_prime)      ; // t7 = M^2
            wide_t t8   = moddouble_core(S, q)                ; // t8 = 2*S
            wide_t T    = modsub_core(t7, t8, q)              ; // T = t7-t8
            result.X    = T                                   ; // X3 = T
            wide_t t9   = modsub_core(S, T, q)                ; // t9 = S-T
            wide_t t10  = moddouble_core(YYYY, q)             ; // t10 = YYYY+YYYY
            t10         = moddouble_core(t10, q)              ; // t10 = t10+t10
            t10         = moddouble_core(t10, q)              ; // t10 = t10+t10
            wide_t t11  = modmul_mont_core(M, t9, q, q_prime) ; // t11 = M*t9
            result.Y    = modsub_core(t11, t10, q)            ; // Y3 = t11-t10
            wide_t t12  = modadd_core(P0.Y, P0.Z, q)          ; // t12 = Y1+Z1
            wide_t t13  = modsq_mont_core(t12, q, q_prime)    ; // t13 = t12^2
            wide_t t14  = modsub_core(t13, YY, q)             ; // t14 = t13-YY
            result.Z    = modsub_core(t14, ZZ, q)             ; // Z3 = t14-ZZ
        } else {
            // otherwise do the addition
            // https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-0.html#addition-add-2007-bl
            wide_t H    = modsub_core(U2, U1, q)                   ; // H = U2-U1
            wide_t t2   = moddouble_core(H, q)                     ; // t2 = 2*H
            wide_t I    = modsq_mont_core(t2, q, q_prime)          ; // I = t2^2
            wide_t J    = modmul_mont_core(H, I, q, q_prime)       ; // J = H*I
            wide_t t3   = modsub_core(S2, S1, q)                   ; // t3 = S2-S1
            wide_t r    = moddouble_core(t3, q)                    ; // r = 2*t3
            wide_t V    = modmul_mont_core(U1, I, q, q_prime)      ; // V = U1*I
            wide_t t4   = modsq_mont_core(r, q, q_prime)           ; // t4 = r^2
            wide_t t5   = moddouble_core(V, q)                     ; // t5 = 2*V
            wide_t t6   = modsub_core(t4, J, q)                    ; // t6 = t4-J
            result.X    = modsub_core(t6, t5, q)                   ; // X3 = t6-t5
            wide_t t7   = modsub_core(V, result.X, q)              ; // t7 = V-X3
            wide_t t8   = modmul_mont_core(S1, J, q, q_prime)      ; // t8 = S1*J
            wide_t t9   = moddouble_core(t8, q)                    ; // t9 = 2*t8
            wide_t t10  = modmul_mont_core(r, t7, q, q_prime)      ; // t10 = r*t7
            result.Y    = modsub_core(t10, t9, q)                  ; // Y3 = t10-t9
            wide_t t11  = modadd_core(P0.Z, P1.Z, q)               ; // t11 = Z1+Z2
            wide_t t12  = modsq_mont_core(t11, q, q_prime)         ; // t12 = t11^2
            wide_t t13  = modsub_core(t12, Z1Z1, q)                ; // t13 = t12-Z1Z1
            wide_t t14  = modsub_core(t13, Z2Z2, q)                ; // t14 = t13-Z2Z2
            result.Z    = modmul_mont_core(t14, H, q, q_prime)     ; // Z3 = t14*H
        }
    }
    return result;
}

#if Q_TYPE == FIXED_Q

EC_point_J point_add_mnt(EC_point_J P0, EC_point_J P1) {
    return point_add_mnt_core(P0, P1, Q, Q_PRIME);
}

#else  // VARIABLE Q

EC_point_J point_add_mnt(
    EC_point_J P0, EC_point_J P1, 
    const wide_t q, const wide_t q_prime
) {
    return point_add_mnt_core(P0, P1, q, q_prime);
}

#endif
