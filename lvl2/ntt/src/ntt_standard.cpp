#include "ntt_standard.h"

void ntt_standard(
    wide_t omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const ModOps& be)
{
#if NTT_STANDARD_VARIANT == NTT_STANDARD_DIF_NR
    ntt_standard_dif_nr(omegas, ping, pong, be);
#elif NTT_STANDARD_VARIANT == NTT_STANDARD_DIF_RN
    ntt_standard_dif_rn(omegas, ping, pong, be);
#elif NTT_STANDARD_VARIANT == NTT_STANDARD_DIT_NR
    ntt_standard_dit_nr(omegas, ping, pong, be);
#elif NTT_STANDARD_VARIANT == NTT_STANDARD_DIT_RN
    ntt_standard_dit_rn(omegas, ping, pong, be);
#endif
}

void intt_standard(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
#if NTT_STANDARD_VARIANT == NTT_STANDARD_DIF_NR
    intt_standard_dif_nr(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_STANDARD_VARIANT == NTT_STANDARD_DIF_RN
    intt_standard_dif_rn(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_STANDARD_VARIANT == NTT_STANDARD_DIT_NR
    intt_standard_dit_nr(inverse_omegas, ping, pong, n_inv, be);
#elif NTT_STANDARD_VARIANT == NTT_STANDARD_DIT_RN
    intt_standard_dit_rn(inverse_omegas, ping, pong, n_inv, be);
#endif
}

void ntt_standard_dif_nr(
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

    int m = NTT_LEN;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        
        int step = m;
        m >>= 1;

        BLOCK: for (int block_start = 0; block_start < NTT_LEN; block_start += step) {
            int twiddle_idx = 0;

            OFFSET: for (int offset = 0; offset < m; offset++) {
                if ((stage % 2) == 0) {
                    upper = ping[block_start + offset];
                    lower = ping[block_start + offset + m];
                } else {
                    upper = pong[block_start + offset];
                    lower = pong[block_start + offset + m];
                }

                omega = omegas[twiddle_idx];

                upper_result = be.modadd(upper, lower);
                lower_input = be.modsub(upper, lower);
                lower_result = be.modmul(lower_input, omega);

                if ((stage % 2) == 0) {
                    pong[block_start + offset] = upper_result;
                    pong[block_start + offset + m] = lower_result;
                } else {
                    ping[block_start + offset] = upper_result;
                    ping[block_start + offset + m] = lower_result;
                }

                twiddle_idx += (NTT_LEN >> (NUM_STAGES - stage));
            }
        }
    }
}

void ntt_standard_dif_rn(
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

    int m = 1;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        int step = m << 1;
        int twiddle_idx;

        BLOCK: for (int block_start = 0; block_start < NTT_LEN; block_start += step) {
            
            twiddle_idx = m * reverse_bits(block_start >> (stage + 1), NUM_STAGES - stage - 1);

            OFFSET: for (int offset = 0; offset < m; offset++) {
                if ((stage % 2) == 0) {
                    upper = ping[block_start + offset];
                    lower = ping[block_start + offset + m];
                } else {
                    upper = pong[block_start + offset];
                    lower = pong[block_start + offset + m];
                }

                omega = omegas[twiddle_idx];

                upper_result = be.modadd(upper, lower);
                lower_input = be.modsub(upper, lower);
                lower_result = be.modmul(lower_input, omega);

                if ((stage % 2) == 0) {
                    pong[block_start + offset] = upper_result;
                    pong[block_start + offset + m] = lower_result;
                } else {
                    ping[block_start + offset] = upper_result;
                    ping[block_start + offset + m] = lower_result;
                }
            }
        }
        m <<= 1;
    }
}

void intt_standard_dif_nr(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_standard_dif_nr(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}

void intt_standard_dif_rn(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_standard_dif_rn(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}

void ntt_standard_dit_nr(
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

    int m = NTT_LEN;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        
        int step = m;
        m >>= 1;
        int twiddle_idx;

        BLOCK: for (int block_start = 0; block_start < NTT_LEN; block_start += step) {
        
            twiddle_idx = m * reverse_bits(block_start >> (NUM_STAGES - stage), stage);
        
            OFFSET: for (int offset = 0; offset < m; offset++) {
                if ((stage % 2) == 0) {
                    upper = ping[block_start + offset];
                    lower = ping[block_start + offset + m];
                } else {
                    upper = pong[block_start + offset];
                    lower = pong[block_start + offset + m];
                }

                omega = omegas[twiddle_idx];

                lower_input = be.modmul(lower, omega);
                upper_result = be.modadd(upper, lower_input);
                lower_result = be.modsub(upper, lower_input);

                if ((stage % 2) == 0) {
                    pong[block_start + offset] = upper_result;
                    pong[block_start + offset + m] = lower_result;
                } else {
                    ping[block_start + offset] = upper_result;
                    ping[block_start + offset + m] = lower_result;
                }
            }
        }
    }
}

void intt_standard_dit_nr(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_standard_dit_nr(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}

void ntt_standard_dit_rn(
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

    int m = 1;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        int step = m << 1;
        int twiddle_idx;
        BLOCK: for (int block_start = 0; block_start < NTT_LEN; block_start += step) {
            
            twiddle_idx = 0;

            OFFSET: for (int offset = 0; offset < m; offset++) {
                if ((stage % 2) == 0) {
                    upper = ping[block_start + offset];
                    lower = ping[block_start + offset + m];
                } else {
                    upper = pong[block_start + offset];
                    lower = pong[block_start + offset + m];
                }

                omega = omegas[twiddle_idx];

                lower_input = be.modmul(lower, omega);
                upper_result = be.modadd(upper, lower_input);
                lower_result = be.modsub(upper, lower_input);

                if ((stage % 2) == 0) {
                    pong[block_start + offset] = upper_result;
                    pong[block_start + offset + m] = lower_result;
                } else {
                    ping[block_start + offset] = upper_result;
                    ping[block_start + offset + m] = lower_result;
                }
                twiddle_idx += (NTT_LEN >> (stage + 1));
            }
        }
        m <<= 1;
    }
}

void intt_standard_dit_rn(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_standard_dit_rn(inverse_omegas, ping, pong, be);
    normalize_intt(ping, pong, n_inv, be);
}
