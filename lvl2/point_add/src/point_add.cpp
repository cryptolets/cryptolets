#include "point_add.h"

// Short Weierstrass Curve with Jacobian coordinates
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
                result = point_double_a_0(P0, be);
            #elif FIELD_A == ANEG3  // a = -3
                result = point_double_a_3(P0, Z1Z1, be);
            #else // for variable a and a = 2
                result = point_double_a_var(P0, be, field_a);
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