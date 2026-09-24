#include "ntt_constant_geometry.h"

void ntt_constant_geometry(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const ModOps& be)
{
#if NTT_CONSTANT_GEOMETRY_VARIANT == NTT_PEASE_DIF
    ntt_dif_pease(omegas, ping, pong, be);
#elif NTT_CONSTANT_GEOMETRY_VARIANT == NTT_PEASE_DIT
    ntt_dit_pease(omegas, ping, pong, be);
#elif NTT_CONSTANT_GEOMETRY_VARIANT == NTT_KORN_LAMBIOTTE_DIF
    ntt_dif_korn_lambiotte(omegas, ping, pong, be);
#elif NTT_CONSTANT_GEOMETRY_VARIANT == NTT_KORN_LAMBIOTTE_DIT
    ntt_dit_korn_lambiotte(omegas, ping, pong, be);
#endif
}

void intt_constant_geometry(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
#if NTT_CONSTANT_GEOMETRY_VARIANT == NTT_PEASE_DIF
    intt_dif_pease(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_CONSTANT_GEOMETRY_VARIANT == NTT_PEASE_DIT
    intt_dit_pease(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_CONSTANT_GEOMETRY_VARIANT == NTT_KORN_LAMBIOTTE_DIF
    intt_dif_korn_lambiotte(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_CONSTANT_GEOMETRY_VARIANT == NTT_KORN_LAMBIOTTE_DIT
    intt_dit_korn_lambiotte(inverse_omegas, ping, pong, n_inv, be);
#endif
}

void ntt_dif_pease(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const ModOps& be)
{
    wide_t upper;
    wide_t lower;
    wide_t omega;
    wide_t lower_input;

    wide_t upper_result;
    wide_t lower_result;

    twiddle_idx_int a_mask = (NTT_LEN >> 1) - 1;
    twiddle_idx_int b_mask = (NTT_LEN >> 1) - 1;
    twiddle_idx_int twiddle_idx;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        BF_COMPUTE: for (int j = 0; j < NTT_LEN/2; j++) {

            if ((stage % 2) == 0) {
                upper = ping[j << 1];
                lower = ping[(j << 1) + 1];
            } else {
                upper = pong[j << 1];
                lower = pong[(j << 1) + 1];
            }

            twiddle_idx = reverse_bits(j, NUM_STAGES - 1) & a_mask;
            omega = omegas[twiddle_idx];

            upper_result = be.modadd(upper, lower);
            lower_input = be.modsub(upper, lower);
            lower_result = be.modmul(lower_input, omega);

            if ((stage % 2) == 0) {
                pong[j] = upper_result;
                pong[j + (NTT_LEN >> 1)] = lower_result;
            } else {
                ping[j] = upper_result;
                ping[j + (NTT_LEN >> 1)] = lower_result;
            }
        }

        a_mask = (a_mask << 1) & b_mask;
    }
}

void intt_dif_pease(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_dif_pease(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}

void ntt_dit_pease(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const ModOps& be)
{
    wide_t upper;
    wide_t lower;
    wide_t omega;
    wide_t lower_input;

    wide_t upper_result;
    wide_t lower_result;

    twiddle_idx_int a_mask = 0;
    twiddle_idx_int b_mask = NTT_LEN >> 2;
    twiddle_idx_int twiddle_idx;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        BF_COMPUTE: for (int j = 0; j < NTT_LEN/2; j++) {

            if ((stage % 2) == 0) {
                upper = ping[j << 1];
                lower = ping[(j << 1) + 1];
            } else {
                upper = pong[j << 1];
                lower = pong[(j << 1) + 1];
            }

            twiddle_idx = j & a_mask;
            omega = omegas[twiddle_idx];

            lower_input = be.modmul(lower, omega);
            upper_result = be.modadd(upper, lower_input);
            lower_result = be.modsub(upper, lower_input);

            if ((stage % 2) == 0) {
                pong[j] = upper_result;
                pong[j + (NTT_LEN >> 1)] = lower_result;
            } else {
                ping[j] = upper_result;
                ping[j + (NTT_LEN >> 1)] = lower_result;
            }
        }
        a_mask |= b_mask;
        b_mask >>= 1;
    }
}

void intt_dit_pease(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_dit_pease(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}

void ntt_dif_korn_lambiotte(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const ModOps& be)
{
    wide_t upper;
    wide_t lower;
    wide_t omega;
    wide_t lower_input;

    wide_t upper_result;
    wide_t lower_result;
    twiddle_idx_int a_mask = (NTT_LEN >> 1) - 1;
    twiddle_idx_int b_mask = (NTT_LEN >> 1) - 1;
    twiddle_idx_int twiddle_idx;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        BF_COMPUTE: for (int j = 0; j < NTT_LEN/2; j++) {
            if ((stage % 2) == 0) {
                upper = ping[j];
                lower = ping[j + (NTT_LEN >> 1)];
            } else {
                upper = pong[j];
                lower = pong[j + (NTT_LEN >> 1)];
            }

            twiddle_idx = j & a_mask;
            omega = omegas[twiddle_idx];

            upper_result = be.modadd(upper, lower);
            lower_input = be.modsub(upper, lower);
            lower_result = be.modmul(lower_input, omega);

            if ((stage % 2) == 0) {
                pong[j << 1] = upper_result;
                pong[(j << 1) + 1] = lower_result;
            } else {
                ping[j << 1] = upper_result;
                ping[(j << 1) + 1] = lower_result;
            }
        }

        a_mask = (a_mask << 1) & b_mask;
    }
}

void intt_dif_korn_lambiotte(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_dif_korn_lambiotte(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}

void ntt_dit_korn_lambiotte(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const ModOps& be)
{
    wide_t upper;
    wide_t lower;
    wide_t omega;
    wide_t lower_input;

    wide_t upper_result;
    wide_t lower_result;

    twiddle_idx_int a_mask = 0;
    twiddle_idx_int b_mask = NTT_LEN >> 2;
    twiddle_idx_int twiddle_idx;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        BF_COMPUTE: for (int j = 0; j < NTT_LEN/2; j++) {
            if ((stage % 2) == 0) {
                upper = ping[j];
                lower = ping[j + (NTT_LEN >> 1)];
            } else {
                upper = pong[j];
                lower = pong[j + (NTT_LEN >> 1)];
            }

            twiddle_idx = reverse_bits(j, NUM_STAGES - 1) & a_mask;
            omega = omegas[twiddle_idx];

            lower_input = be.modmul(lower, omega);
            upper_result = be.modadd(upper, lower_input);
            lower_result = be.modsub(upper, lower_input);

            if ((stage % 2) == 0) {
                pong[j << 1] = upper_result;
                pong[(j << 1) + 1] = lower_result;
            } else {
                ping[j << 1] = upper_result;
                ping[(j << 1) + 1] = lower_result;
            }
        }

        a_mask |= b_mask;
        b_mask >>= 1;
    }
}

void intt_dit_korn_lambiotte(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_dit_korn_lambiotte(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}
