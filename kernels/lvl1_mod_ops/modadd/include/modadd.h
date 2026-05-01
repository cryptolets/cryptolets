#ifndef _MODADD_H_
#define _MODADD_H_

#include "primitives.h"

ac_int<N, false> modadd_inst(
    const ac_int<N, false> a, 
    const ac_int<N, false> b, 
    const ac_int<N, false> q
);

template<int N, bool MULTI_WORD = false, int BASE = 32>
ac_int<N, false> modadd(
    const ac_int<N, false> a, 
    const ac_int<N, false> b, 
    const ac_int<N, false> q
) {
    ac_int<N+1, false> adder_out = a + b;
    ac_int<N+1, true> reduced_out = adder_out - q;

    // Use reduced_out only if non-negative
    return (!reduced_out[N]) ? (ac_int<N, false>)reduced_out : 
                               (ac_int<N, false>)adder_out;
}

#endif /* _MODADD_H_ */
