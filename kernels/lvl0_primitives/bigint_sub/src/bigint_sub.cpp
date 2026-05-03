#include "bigint_sub.h"

ac_int<N+1, true> bigint_sub_inst(
    const ac_int<N, false> x,
    const ac_int<N, false> y
) {
    return bigint_sub<N>(x, y);
}