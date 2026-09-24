#ifndef _NTT_CONSTANT_GEOMETRY_H_
#define _NTT_CONSTANT_GEOMETRY_H_

#include "ntt_common.h"

void ntt_constant_geometry(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_constant_geometry(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_dif_pease(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_dif_pease(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_dit_pease(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_dit_pease(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_dif_korn_lambiotte(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_dif_korn_lambiotte(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

void ntt_dit_korn_lambiotte(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be);

void intt_dit_korn_lambiotte(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

#endif /* _NTT_CONSTANT_GEOMETRY_H_ */
