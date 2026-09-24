#ifndef _NTT_STANDARD_H_
#define _NTT_STANDARD_H_

#include "ntt_common.h"

void ntt_standard(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_standard(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_standard_dif_nr(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_standard_dif_nr(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_standard_dif_rn(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_standard_dif_rn(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_standard_dit_nr(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_standard_dit_nr(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_standard_dit_rn(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_standard_dit_rn(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

#endif /* _NTT_STANDARD_H_ */
