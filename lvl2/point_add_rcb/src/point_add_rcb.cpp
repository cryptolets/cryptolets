#include "point_add_rcb.h"

// Short Weierstrass Curve with Mixed Projective-Affine coordinates
// Source: https://eprint.iacr.org/2015/1060.pdf (Algorithm 8)
// Assumes a = 0

EC_point_P point_add_rcb_core(
    EC_point_P P0, EC_point_A P1,
    const ModOps& be, 
    const wide_t field_b3
) {
    EC_point_P result;
    
    wide_t t0 = be.modmul(P0.X, P1.x);      //  1. t0 = X1*x2
    wide_t t1 = be.modmul(P0.Y, P1.y);      //  2. t1 = Y1*y2
    wide_t t3 = be.modadd(P1.x, P1.y);      //  3. t3 = x2+y2
    wide_t t4 = be.modadd(P0.X, P0.Y);      //  4. t4 = X1+Y1
    t3        = be.modmul(t3, t4);          //  5. t3 = t3*t4
    t4        = be.modadd(t0, t1);          //  6. t4 = t0+t1
    t3        = be.modsub(t3, t4);          //  7. t3 = t3-t4
    t4        = be.modmul(P1.y, P0.Z);      //  8. t4 = y2*Z1
    t4        = be.modadd(t4, P0.Y);        //  9. t4 = t4+Y1
    result.Y  = be.modmul(P1.x, P0.Z);      // 10. Y3 = x2*Z1
    result.Y  = be.modadd(result.Y, P0.X);  // 11. Y3 = Y3+X1
    result.X  = be.moddouble(t0);           // 12. X3 = t0+t0
    t0        = be.modadd(result.X, t0);    // 13. t0 = X3+t0

    #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
        wide_t t2 = be.cmodmul_b3(P0.Z);        // 14. t2 = b3*Z1 (const)
    #else
        wide_t t2 = be.modmul(field_b3, P0.Z);  // 14. t2 = b3*Z1
    #endif

    result.Z  = be.modadd(t1, t2);          // 15. Z3 = t1+t2
    t1        = be.modsub(t1, t2);          // 16. t1 = t1-t2

    #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
        result.Y = be.cmodmul_b3(result.Y);        // 17. Y3 = b3*Y3 (const)
    #else
        result.Y = be.modmul(field_b3, result.Y);  // 17. Y3 = b3*Y3
    #endif

    result.X  = be.modmul(t4, result.Y);    // 18. X3 = t4*Y3
    t2        = be.modmul(t3, t1);          // 19. t2 = t3*t1
    result.X  = be.modsub(t2, result.X);    // 20. X3 = t2-X3
    result.Y  = be.modmul(result.Y, t0);    // 21. Y3 = Y3*t0
    t1        = be.modmul(t1, result.Z);    // 22. t1 = t1*Z3
    result.Y  = be.modadd(t1, result.Y);    // 23. Y3 = t1+Y3
    t0        = be.modmul(t0, t3);          // 24. t0 = t0*t3
    result.Z  = be.modmul(result.Z, t4);    // 25. Z3 = Z3*t4
    result.Z  = be.modadd(result.Z, t0);    // 26. Z3 = Z3+t0
    return result;
}

// Public API

EC_point_P point_add_rcb(
    EC_point_P P0, EC_point_A P1 

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

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS)
    , const wide_t field_b3
#endif

) {
    #if Q_TYPE == FIXED_Q
        const wide_t q = Q;
    #endif

    #if !(CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS)
        #if MODMUL_TYPE == MODMUL_TYPE_MONT
            const wide_t field_b3 = FIELD_B3_MONT;
        #else
            const wide_t field_b3 = FIELD_B3_INT;
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

    return point_add_rcb_core(P0, P1, be, field_b3);
}
