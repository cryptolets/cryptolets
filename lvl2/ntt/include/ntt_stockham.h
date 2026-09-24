#ifndef _NTT_STOCKHAM_H_
#define _NTT_STOCKHAM_H_

#include "ntt_common.h"

void ntt_stockham_dif(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_stockham_dif(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_stockham_dit(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_stockham_dit(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

#endif /* _NTT_STOCKHAM_H_ */
