#include "ntt_common.h"


int reverse_bits(int number, int bit_length)
{
    int reversed = 0;

    REVERSE_BITS: for (int i = 0; i < bit_length; i++) {
        if ((number >> i) & 1) {
            reversed |= 1 << (bit_length - 1 - i);
        }
    }

    return reversed;
}

void normalize_intt(
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be)
{
    if ((NUM_STAGES % 2) == 0) {
        NORMALIZE_PING: for (int i = 0; i < NTT_LEN; i++) {
            ping[i] = be.modmul(ping[i], n_inv);
        }
    } else {
        NORMALIZE_PONG: for (int i = 0; i < NTT_LEN; i++) {
            pong[i] = be.modmul(pong[i], n_inv);
        }
    }
}
