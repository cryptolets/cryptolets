#include "modadd.h"

ac_int<N, false> modadd_inst(
    const ac_int<N, false> a, 
    const ac_int<N, false> b, 
    const ac_int<N, false> q
) {
    return modadd<N>(a, b, q);
}