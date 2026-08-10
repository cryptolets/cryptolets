#ifndef _NTT_H_
#define _NTT_H_

#include "ntt_common.h"
#include "ntt_standard.h"
#include "ntt_constant_geometry.h"
#include "ntt_stockham.h"

void ntt_core(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_core(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN]

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
);

void intt(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
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
);

#endif /* _NTT_H_ */
