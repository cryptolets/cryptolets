#include "point_add_te.h"

// Twisted Edwards Curve with Extended coordinates

EC_point_EP point_add_te_core(
    EC_point_EP P0, EC_point_EP P1,
    const ModOps& be, 
    const wide_t field_a, const wide_t field_d, const wide_t field_k
) {
    EC_point_EP result;

#if FIELD_A == ANEG1 
    // a = -1
    // https://hyperelliptic.org/EFD/g1p/auto-twisted-extended-1.html#addition-add-2008-hwcd-3
    
    wide_t t0 = be.modsub(P0.Y, P0.X)             ; // t0 = Y1-X1
    wide_t t1 = be.modsub(P1.Y, P1.X)             ; // t1 = Y2-X2
    wide_t A  = be.modmul(t0, t1)                 ; // A = t0*t1
    wide_t t2 = be.modadd(P0.Y, P0.X)             ; // t2 = Y1+X1
    wide_t t3 = be.modadd(P1.Y, P1.X)             ; // t3 = Y2+X2
    wide_t B  = be.modmul(t2, t3)                 ; // B = t2*t3
    #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
        wide_t t4 = be.cmodmul_k(P1.T)            ; // t4 = k*T2 (const)
    #else
        wide_t t4 = be.modmul(field_k, P1.T)      ; // t4 = k*T2 (const)
    #endif
    wide_t C  = be.modmul(P0.T, t4)               ; // C = T1*t4
    wide_t t5 = be.moddouble(P1.Z)                ; // t5 = 2*Z2
    wide_t D  = be.modmul(P0.Z, t5)               ; // D = Z1*t5
    wide_t E  = be.modsub(B, A)                   ; // E = B-A
    wide_t F  = be.modsub(D, C)                   ; // F = D-C
    wide_t G  = be.modadd(D, C)                   ; // G = D+C
    wide_t H  = be.modadd(B, A)                   ; // H = B+A
    result.X  = be.modmul(E, F)                   ; // X3 = E*F
    result.Y  = be.modmul(G, H)                   ; // Y3 = G*H
    result.T  = be.modmul(E, H)                   ; // T3 = E*H
    result.Z  = be.modmul(F, G)                   ; // Z3 = F*G
#else
    // variable a
    // https://hyperelliptic.org/EFD/g1p/auto-twisted-extended.html#addition-add-2008-hwcd

    wide_t A  = be.modmul(P0.X, P1.X)              ; // A = X1*X2
    wide_t B  = be.modmul(P0.Y, P1.Y)              ; // B = Y1*Y2
    #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
        wide_t t0 = be.cmodmul_d(P1.T)             ; // t0 = d*T2 (const)
    #else
        wide_t t0 = be.modmul(field_d, P1.T)       ; // t0 = d*T2 (const)
    #endif
    wide_t C  = be.modmul(P0.T, t0)                ; // C = T1*t0
    wide_t D  = be.modmul(P0.Z, P1.Z)              ; // D = Z1*Z2
    wide_t t1 = be.modadd(P0.X, P0.Y)              ; // t1 = X1+Y1
    wide_t t2 = be.modadd(P1.X, P1.Y)              ; // t2 = X2+Y2
    wide_t t3 = be.modmul(t1, t2)                  ; // t3 = t1*t2
    wide_t t4 = be.modsub(t3, A)                   ; // t4 = t3-A
    wide_t E  = be.modsub(t4, B)                   ; // E = t4-B
    wide_t F  = be.modsub(D, C)                    ; // F = D-C
    wide_t G  = be.modadd(D, C)                    ; // G = D+C
    #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
        wide_t t5 = be.cmodmul_a(A)                ; // t5 = a*A (const)
    #else
        wide_t t5 = be.modmul(field_a, A)          ; // t5 = a*A (const)
    #endif
    wide_t H  = be.modsub(B, t5)                   ; // H = B-t5
    result.X  = be.modmul(E, F)                    ; // X3 = E*F
    result.Y  = be.modmul(G, H)                    ; // Y3 = G*H
    result.T  = be.modmul(E, H)                    ; // T3 = E*H
    result.Z  = be.modmul(F, G)                    ; // Z3 = F*G
#endif

    return result;
}

// Public API

EC_point_EP point_add_te(
    EC_point_EP P0, EC_point_EP P1 

#if Q_TYPE == VAR_Q
    , const wide_t q
#endif

#if REDC_TYPE == VAR_RC
    , const wide_t q_prime
#endif

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == AVAR)
    , const wide_t field_a, const wide_t field_d
#endif

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == ANEG1)
    , const wide_t field_k
#endif

) {
    #if Q_TYPE == FIXED_Q
        const wide_t q = Q;
    #endif

    #if !((CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == AVAR))
        #if MODMUL_TYPE == MODMUL_TYPE_MONT
            const wide_t field_a = FIELD_A_MONT;
            const wide_t field_d = FIELD_D_MONT;
        #else
            const wide_t field_a = FIELD_A_INT;
            const wide_t field_d = FIELD_D_INT;
        #endif
    #endif

    #if !((CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == ANEG1))
        #if MODMUL_TYPE == MODMUL_TYPE_MONT
            const wide_t field_k = FIELD_K_MONT;
        #else
            const wide_t field_k = FIELD_K_INT;
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

    return point_add_te_core(P0, P1, be, field_a, field_d, field_k);
}