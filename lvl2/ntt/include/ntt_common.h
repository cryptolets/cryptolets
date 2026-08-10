#ifndef _NTT_COMMON_H_
#define _NTT_COMMON_H_

#include "primitives.h"
#include "modops.h"

#ifndef NUM_STAGES
    #define NUM_STAGES ac::log2_ceil<NTT_LEN>::val
#endif

#ifndef NTT_STANDARD_VARIANT
    #define NTT_STANDARD_VARIANT NTT_STANDARD_DIT_RN
#endif

#ifndef NTT_CONSTANT_GEOMETRY_VARIANT
    #define NTT_CONSTANT_GEOMETRY_VARIANT NTT_PEASE_DIT
#endif

#define NUM_IDX_BITS ac::log2_ceil<NTT_LEN>::val

typedef ac_int<NUM_IDX_BITS - 1, false> twiddle_idx_int;

int reverse_bits(int number, int bit_length);

void normalize_intt(
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    const wide_t n_inv,
    const ModOps& be);

#endif /* _NTT_COMMON_H_ */
