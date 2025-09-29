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
    #if Q_TYPE == FIXED_Q
        wide_t t4 = be.cmodmul(field_k, P1.T)     ; // t4 = k*T2 (const)
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
    #if Q_TYPE == FIXED_Q
        wide_t t0 = be.cmodmul(field_d, P1.T)      ; // t0 = d*T2 (const)
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
    #if FIELD_A == AVAR
        wide_t t5 = be.cmodmul(field_a, A)         ; // t5 = a*A (const)
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


#if Q_TYPE == FIXED_Q
    EC_point_EP point_add_te(
        EC_point_EP P0, EC_point_EP P1
    ) {
        // Declare modops backend
        #if MODMUL_TYPE == MODMUL_TYPE_MONT
            ModOps be(Q, Q_PRIME);
        #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
            ModOps be(Q, MU);
        #endif

        return point_add_te_core(P0, P1, be, FIELD_A_MONT, FIELD_D_MONT, FIELD_K_MONT);
    }
#else // Q_TYPE == VAR_Q
    #if FIELD_A == ANEG1
        EC_point_EP point_add_te(
            EC_point_EP P0, EC_point_EP P1, 
            const wide_t q, const wide_t q_prime,
            const wide_t field_k
        ) {
            // Declare modops backend
            #if MODMUL_TYPE == MODMUL_TYPE_MONT
                ModOps be(q, q_prime);
            #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
                ModOps be(q, mu);
            #endif

            return point_add_te_core(P0, P1, be, FIELD_A_MONT, FIELD_D_MONT, field_k);
        }
    #elif FIELD_A == AVAR
        EC_point_EP point_add_te(
            EC_point_EP P0, EC_point_EP P1, 
            const wide_t q, const wide_t q_prime,
            const wide_t field_a, const wide_t field_d
        ) {
            // Declare modops backend
            #if MODMUL_TYPE == MODMUL_TYPE_MONT
                ModOps be(q, q_prime);
            #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
                ModOps be(q, mu);
            #endif

            return point_add_te_core(P0, P1, be, field_a, field_d, FIELD_K_MONT);
        }
    #else
        EC_point_EP point_add_te(
            EC_point_EP P0, EC_point_EP P1,
            const wide_t q, const wide_t q_prime
        ) {
            // Declare modops backend
            #if MODMUL_TYPE == MODMUL_TYPE_MONT
                ModOps be(q, q_prime);
            #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
                ModOps be(q, mu);
            #endif

            return point_add_te_core(P0, P1, be, FIELD_A_MONT, FIELD_D_MONT, FIELD_K_MONT);
        }
    #endif
#endif
