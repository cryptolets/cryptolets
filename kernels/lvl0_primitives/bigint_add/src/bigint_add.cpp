#include "bigint_add.h"

ac_int<N+1, false> bigint_add_inst(
    const ac_int<N, false> x,
    const ac_int<N, false> y
) {
    return bigint_add<N>(x, y);
}