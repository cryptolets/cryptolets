#include "point_add_cyclonemsm.h"

// CycloneMSM Implementation

EC_point_EP point_add_cyclonemsm_core(
    EC_point_EP P0, 
    EC_point_EA P1,
    const ModOps& be
) {
    // https://github.com/JumpCrypto/cyclone/blob/main/msm/src/preprocess.rs#L91

    EC_point_EP result;

    // step 1
    wide_t r1 = be.modsub(P0.Y, P0.X);     // r1 = Y1 - X1
    wide_t r2 = be.modsub(P1.y, P1.x);     // r2 = y2 - x2
    wide_t r3 = be.modadd(P0.Y, P0.X);     // r3 = Y1 + X1
    wide_t r4 = be.modadd(P1.y, P1.x);     // r4 = y2 + x2

    // step 2
    wide_t r5 = be.modmul(r1, r2);         // r5 = r1 * r2
    wide_t r6 = be.modmul(r3, r4);         // r6 = r3 * r4
    wide_t r7 = be.modmul(P0.T, P1.u);     // r7 = T1 * u2
    wide_t r8 = be.moddouble(P0.Z);        // r8 = 2 * Z1

    // step 3
    wide_t r1b = be.modsub(r6, r5);        // r1b = r6 - r5
    wide_t r2b = be.modsub(r8, r7);        // r2b = r8 - r7
    wide_t r3b = be.modadd(r8, r7);        // r3b = r8 + r7
    wide_t r4b = be.modadd(r6, r5);        // r4b = r6 + r5

    // step 4
    result.X = be.modmul(r1b, r2b);        // X3 = r1b * r2b
    result.Y = be.modmul(r3b, r4b);        // Y3 = r3b * r4b
    result.Z = be.modmul(r2b, r3b);        // Z3 = r2b * r3b
    result.T = be.modmul(r1b, r4b);        // T3 = r1b * r4b

    return result;
}

// Public API

EC_point_EP point_add_cyclonemsm(
    EC_point_EP P0, EC_point_EA P1 

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
) {
    #if Q_TYPE == FIXED_Q
        const wide_t q = Q;
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

    return point_add_cyclonemsm_core(P0, P1, be);
}

