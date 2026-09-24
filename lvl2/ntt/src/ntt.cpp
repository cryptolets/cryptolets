#include "ntt.h"

void ntt_core(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const ModOps& be)
{
#if NTT_IMPL == NTT_IMPL_STANDARD
    ntt_standard(omegas, ping, pong, be);
#elif NTT_IMPL == NTT_IMPL_CONSTANT_GEOMETRY
    ntt_constant_geometry(omegas, ping, pong, be);
#elif NTT_IMPL == NTT_IMPL_STOCKHAM
    #if NTT_STOCKHAM_VARIANT == NTT_STOCKHAM_DIF
    ntt_stockham_dif(omegas, ping, pong, be);
    #elif NTT_STOCKHAM_VARIANT == NTT_STOCKHAM_DIT
    ntt_stockham_dit(omegas, ping, pong, be);
    #endif
#endif
}

void intt_core(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
#if NTT_IMPL == NTT_IMPL_STANDARD
    intt_standard(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_IMPL == NTT_IMPL_CONSTANT_GEOMETRY
    intt_constant_geometry(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_IMPL == NTT_IMPL_STOCKHAM
    #if NTT_STOCKHAM_VARIANT == NTT_STOCKHAM_DIF
    intt_stockham_dif(inverse_omegas, ping, pong, n_inv, be);
    #elif NTT_STOCKHAM_VARIANT == NTT_STOCKHAM_DIT
    intt_stockham_dit(inverse_omegas, ping, pong, n_inv, be);
    #endif
#endif
}

void ntt(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN]

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

    ntt_core(omegas, ping, pong, be);
}

void intt(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv

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

    intt_core(inverse_omegas, ping, pong, n_inv, be);
}
