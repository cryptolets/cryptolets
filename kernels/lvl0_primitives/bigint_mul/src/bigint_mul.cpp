#include "bigint_mul.h"

template ac_int<2*N, false> bigint_mul<N, MULTI_WORD>(
    ac_int<N, false>,
    ac_int<N, false>
);
