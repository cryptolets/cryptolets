#include "ntt_stockham.h"


void ntt_stockham_dif(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be)
{
    wide_t upper;
    wide_t lower;
    wide_t omega;
    wide_t lower_input;

    wide_t upper_result;
    wide_t lower_result;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        int log_n = NUM_STAGES;
        int n = NTT_LEN;
        int groups = 1 << stage;
        int stride = n >> (stage + 1);
        int lane_shift = log_n - 1 - stage;

        BF_COMPUTE: for (int butterfly_idx = 0; butterfly_idx < (n >> 1); butterfly_idx++) {
            int group = butterfly_idx >> lane_shift;
            int lane = butterfly_idx & (stride - 1);

            int upper_read_idx = lane + (group << (log_n - stage));
            int lower_read_idx = upper_read_idx + stride;

            if ((stage % 2) == 0) {
                upper = in[upper_read_idx];
                lower = in[lower_read_idx];
            } else {
                upper = out[upper_read_idx];
                lower = out[lower_read_idx];
            }

            twiddle_idx_int twiddle_idx = lane * groups;
            omega = omegas[twiddle_idx];

            upper_result = be.modadd(upper, lower);
            lower_input = be.modsub(upper, lower);
            lower_result = be.modmul(lower_input, omega);

            int upper_write_idx = butterfly_idx;
            int lower_write_idx = butterfly_idx + (n >> 1);

            if ((stage % 2) == 0) {
                out[upper_write_idx] = upper_result;
                out[lower_write_idx] = lower_result;
            } else {
                in[upper_write_idx] = upper_result;
                in[lower_write_idx] = lower_result;
            }
        }
    }
}

void intt_stockham_dif(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_stockham_dif(inverse_omegas, in, out, be);
    normalize_intt(in, out, n_inv, be);
}

void ntt_stockham_dit(
    wide_t omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const ModOps& be)
{
    wide_t upper;
    wide_t lower;
    wide_t omega;
    wide_t lower_twiddled;

    wide_t upper_result;
    wide_t lower_result;

    STAGE: for (int stage = 0; stage < NUM_STAGES; stage++) {
        int log_n = NUM_STAGES;
        int n = NTT_LEN;
        int stride = n >> (stage + 1);
        int lane_shift = log_n - 1 - stage;

        BF_COMPUTE: for (int butterfly_idx = 0; butterfly_idx < (n >> 1); butterfly_idx++) {
            int group = butterfly_idx >> lane_shift;
            int lane = butterfly_idx & (stride - 1);

            int upper_read_idx = lane + (group << (log_n - stage));
            int lower_read_idx = upper_read_idx + stride;

            if ((stage % 2) == 0) {
                upper = in[upper_read_idx];
                lower = in[lower_read_idx];
            } else {
                upper = out[upper_read_idx];
                lower = out[lower_read_idx];
            }

            twiddle_idx_int twiddle_idx = group * stride;
            omega = omegas[twiddle_idx];

            lower_twiddled = be.modmul(omega, lower);

            upper_result = be.modadd(upper, lower_twiddled);
            lower_result = be.modsub(upper, lower_twiddled);

            int upper_write_idx = butterfly_idx;
            int lower_write_idx = butterfly_idx + (n >> 1);

            if ((stage % 2) == 0) {
                out[upper_write_idx] = upper_result;
                out[lower_write_idx] = lower_result;
            } else {
                in[upper_write_idx] = upper_result;
                in[lower_write_idx] = lower_result;
            }
        }
    }
}

void intt_stockham_dit(
    wide_t inverse_omegas[NTT_LEN/2],
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    ntt_stockham_dit(inverse_omegas, in, out, be);
    normalize_intt(in, out, n_inv, be);
}
