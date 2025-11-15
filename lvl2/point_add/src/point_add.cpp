#include "point_add.h"

// Short Weierstrass Curve with Jacobian coordinates

EC_point_J point_dbl_2009_l_a_0(EC_point_J P0, const ModOps& be) {
    // point doubling for a=0
    // https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-0.html#doubling-dbl-2009-l
    EC_point_J result;
    wide_t A  = be.modsq(P0.X)                      ; // A = X1^2
    wide_t B  = be.modsq(P0.Y)                      ; // B = Y1^2
    wide_t C  = be.modsq(B)                         ; // C = B^2
    wide_t t0 = be.modadd(P0.X, B)                  ; // t0 = X1+B
    wide_t t1 = be.modsq(t0)                        ; // t1 = t0^2
    wide_t t2 = be.modsub(t1, A)                    ; // t2 = t1-A
    wide_t t3 = be.modsub(t2, C)                    ; // t3 = t2-C
    wide_t D  = be.moddouble(t3)                    ; // D = 2*t3
    wide_t E  = be.moddouble(A)                     ; // E = A+A
    E         = be.modadd(E, A)                     ; // E = E+A
    wide_t F  = be.modsq(E)                         ; // F = E^2
    wide_t t4 = be.moddouble(D)                     ; // t4 = 2*D
    result.X  = be.modsub(F, t4)                    ; // X3 = F-t4
    wide_t t5 = be.modsub(D, result.X)              ; // t5 = D-X3
    wide_t t6 = be.moddouble(C)                     ; // t6 = C+C
    t6        = be.moddouble(t6)                    ; // t6 = t6+t6
    t6        = be.moddouble(t6)                    ; // t6 = t6+t6
    wide_t t7 = be.modmul(E, t5)                    ; // t7 = E*t5
    result.Y  = be.modsub(t7, t6)                   ; // Y3 = t7-t6
    wide_t t8 = be.modmul(P0.Y, P0.Z)               ; // t8 = Y1*Z1
    result.Z  = be.moddouble(t8)                    ; // Z3 = 2*t8
    return result;
}

EC_point_J point_dbl_2009_l_a_3(
    EC_point_J P0, 
    const wide_t delta, const ModOps& be
) {
    // point doubling for a=-3
    // https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-3.html#doubling-dbl-2001-b
    EC_point_J result;
    // wide_t delta = modsq_mont(P0.Z)                     ; // delta = Z1^2
    wide_t gamma = be.modsq(P0.Y)                       ; // gamma = Y1^2
    wide_t beta  = be.modmul(P0.X, gamma)               ; // beta = X1*gamma
    wide_t t0    = be.modsub(P0.X, delta)               ; // t0 = X1-delta
    wide_t t1    = be.modadd(P0.X, delta)               ; // t1 = X1+delta
    wide_t t2    = be.modmul(t0, t1)                    ; // t2 = t0*t1
    wide_t alpha = be.moddouble(t2)                     ; // alpha = t2+t2
    alpha        = be.modadd(t2, alpha)                 ; // alpha = t2+alpha
    wide_t t3    = be.modsq(alpha)                      ; // t3 = alpha^2
    wide_t t4    = be.moddouble(beta)                   ; // t4 = beta+beta
    wide_t t8    = be.moddouble(t4)                     ; // t8 = t4+t4
    t4           = be.moddouble(t8)                     ; // t4 = t8+t8
    result.X     = be.modsub(t3, t4)                    ; // X3 = t3-t4
    wide_t t5    = be.modadd(P0.Y, P0.Z)                ; // t5 = Y1+Z1
    wide_t t6    = be.modsq(t5)                         ; // t6 = t5^2
    wide_t t7    = be.modsub(t6, gamma)                 ; // t7 = t6-gamma
    result.Z     = be.modsub(t7, delta)                 ; // Z3 = t7-delta
    wide_t t9    = be.modsub(t8, result.X)              ; // t9 = t8-X3
    wide_t t10   = be.modsq(gamma)                      ; // t10 = gamma^2
    wide_t t11   = be.moddouble(t10)                    ; // t11 = t10+t10
    t11          = be.moddouble(t11)                    ; // t11 = t11+t11
    t11          = be.moddouble(t11)                    ; // t11 = t11+t11
    wide_t t12   = be.modmul(alpha, t9)                 ; // t12 = alpha*t9
    result.Y     = be.modsub(t12, t11)                  ; // Y3 = t12-t11
    return result;
}

EC_point_J point_dbl_2009_l_a_var(
    EC_point_J P0, 
    const ModOps& be, const wide_t field_a
) {
    // point doubling for variable a and a=2
    // Note: this is a general formula; 2*A mod q translates to A+A mod q, which is easy in hardware
    // https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian.html#doubling-dbl-2007-bl
    EC_point_J result;
    wide_t XX   = be.modsq(P0.X)                 ; // XX = X1^2
    wide_t YY   = be.modsq(P0.Y)                 ; // YY = Y1^2
    wide_t YYYY = be.modsq(YY)                   ; // YYYY = YY^2
    wide_t ZZ   = be.modsq(P0.Z)                 ; // ZZ = Z1^2
    wide_t t0   = be.modadd(P0.X, YY)            ; // t0 = X1+YY
    wide_t t1   = be.modsq(t0)                   ; // t1 = t0^2
    wide_t t2   = be.modsub(t1, XX)              ; // t2 = t1-XX
    wide_t t3   = be.modsub(t2, YYYY)            ; // t3 = t2-YYYY
    wide_t S    = be.moddouble(t3)               ; // S = 2*t3
    wide_t t4   = be.modsq(ZZ)                   ; // t4 = ZZ^2

    // t5 = a*t4
    #if FIELD_A == A2
        wide_t t5   = be.moddouble(t4);
    #else // FIELD_A == AVAR
        #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
            wide_t t5   = be.cmodmul_a(t4);
        #else
            wide_t t5   = be.modmul(field_a, t4);
        #endif
    #endif

    wide_t t6   = be.moddouble(XX)               ; // t6 = XX+XX
    t6          = be.modadd(t6, XX)              ; // t6 = t6+XX
    wide_t M    = be.modadd(t6, t5)              ; // M = t6+t5
    wide_t t7   = be.modsq(M)                    ; // t7 = M^2
    wide_t t8   = be.moddouble(S)                ; // t8 = 2*S
    wide_t T    = be.modsub(t7, t8)              ; // T = t7-t8
    result.X    = T                              ; // X3 = T
    wide_t t9   = be.modsub(S, T)                ; // t9 = S-T
    wide_t t10  = be.moddouble(YYYY)             ; // t10 = YYYY+YYYY
    t10         = be.moddouble(t10)              ; // t10 = t10+t10
    t10         = be.moddouble(t10)              ; // t10 = t10+t10
    wide_t t11  = be.modmul(M, t9)               ; // t11 = M*t9
    result.Y    = be.modsub(t11, t10)            ; // Y3 = t11-t10
    wide_t t12  = be.modadd(P0.Y, P0.Z)          ; // t12 = Y1+Z1
    wide_t t13  = be.modsq(t12)                  ; // t13 = t12^2
    wide_t t14  = be.modsub(t13, YY)             ; // t14 = t13-YY
    result.Z    = be.modsub(t14, ZZ)             ; // Z3 = t14-ZZ
    return result;
}


EC_point_J point_add_core(
    EC_point_J P0, EC_point_J P1, const ModOps& be, const wide_t field_a
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
        wide_t Z1Z1 = be.modsq(P0.Z)        ; // Z1Z1 = Z1^2
        wide_t Z2Z2 = be.modsq(P1.Z)        ; // Z2Z2 = Z2^2
        wide_t U1   = be.modmul(P0.X, Z2Z2) ; // U1 = X1*Z2Z2
        wide_t U2   = be.modmul(P1.X, Z1Z1) ; // U2 = X2*Z1Z1
        wide_t t0   = be.modmul(P1.Z, Z2Z2) ; // t0 = Z2*Z2Z2
        wide_t S1   = be.modmul(P0.Y, t0)   ; // S1 = Y1*t0
        wide_t t1   = be.modmul(P0.Z, Z1Z1) ; // t1 = Z1*Z1Z1
        wide_t S2   = be.modmul(P1.Y, t1)   ; // S2 = Y2*t1

        // if equal, run the doubling algorithm
        if (U1 == U2 && S1 == S2) {
            #if FIELD_A == A0       // a = 0
                result = point_dbl_2009_l_a_0(P0, be);
            #elif FIELD_A == ANEG3  // a = -3
                result = point_dbl_2009_l_a_3(P0, Z1Z1, be);
            #else // for variable a and a = 2
                result = point_dbl_2009_l_a_var(P0, be, field_a);
            #endif
        } else {
            // otherwise do the addition
            // point addition is the same for a=0, a=2, and a=-3
            // https://www.hyperelliptic.org/EFD/g1p/auto-shortw-jacobian-0.html#addition-add-2007-bl
            wide_t H    = be.modsub(U2, U1)                   ; // H = U2-U1
            wide_t t2   = be.moddouble(H)                     ; // t2 = 2*H
            wide_t I    = be.modsq(t2)                        ; // I = t2^2
            wide_t J    = be.modmul(H, I)                     ; // J = H*I
            wide_t t3   = be.modsub(S2, S1)                   ; // t3 = S2-S1
            wide_t r    = be.moddouble(t3)                    ; // r = 2*t3
            wide_t V    = be.modmul(U1, I)                    ; // V = U1*I
            wide_t t4   = be.modsq(r)                         ; // t4 = r^2
            wide_t t5   = be.moddouble(V)                     ; // t5 = 2*V
            wide_t t6   = be.modsub(t4, J)                    ; // t6 = t4-J
            result.X    = be.modsub(t6, t5)                   ; // X3 = t6-t5
            wide_t t7   = be.modsub(V, result.X)              ; // t7 = V-X3
            wide_t t8   = be.modmul(S1, J)                    ; // t8 = S1*J
            wide_t t9   = be.moddouble(t8)                    ; // t9 = 2*t8
            wide_t t10  = be.modmul(r, t7)                    ; // t10 = r*t7
            result.Y    = be.modsub(t10, t9)                  ; // Y3 = t10-t9
            wide_t t11  = be.modadd(P0.Z, P1.Z)               ; // t11 = Z1+Z2
            wide_t t12  = be.modsq(t11)                       ; // t12 = t11^2
            wide_t t13  = be.modsub(t12, Z1Z1)                ; // t13 = t12-Z1Z1
            wide_t t14  = be.modsub(t13, Z2Z2)                ; // t14 = t13-Z2Z2
            result.Z    = be.modmul(t14, H)                   ; // Z3 = t14*H
        }
    }
    return result;
}

EC_point_J point_add(
    EC_point_J P0, EC_point_J P1

#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    #if MODMUL_TYPE == MODMUL_TYPE_MONT
        , const wide_t q_prime
    #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
        , const wide_2x_t mu
    #endif
#endif

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == AVAR)
    , const wide_t field_a
#endif

) {
    #if Q_TYPE == FIXED_Q
        const wide_t q = Q;
    #endif

    #if !((CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == AVAR))
        #if MODMUL_TYPE == MODMUL_TYPE_MONT
            const wide_t field_a = FIELD_A_MONT;
        #else
            const wide_t field_a = FIELD_A_INT;
        #endif
    #endif

    // Declare modops backend
    #if MODMUL_TYPE == MODMUL_TYPE_MONT
        #if REDC_TYPE == FIXED_RC
            const wide_t q_prime = Q_PRIME;
        #endif
        
        ModOps be(q, q_prime);
    #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
        #if REDC_TYPE == FIXED_RC
            const wide_2x_t mu = MU;
        #endif
        
        ModOps be(q, mu);
    #endif

    return point_add_core(P0, P1, be, field_a);
}