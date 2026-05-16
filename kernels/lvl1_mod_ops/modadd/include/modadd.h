#ifndef _MODADD_H_
#define _MODADD_H_

#include <ac_int.h>
#include "params.h"
#include "bigint_add.h"
#include "bigint_sub.h"

template<int _N, bool _MULTI_WORD = false, int _BASE = 32>
ac_int<_N, false> modadd(
    const ac_int<_N, false> a, 
    const ac_int<_N, false> b, 
    const ac_int<_N, false> q
) {
    ac_int<_N+1, false> adder_out = bigint_add<_N>(a, b);
    ac_int<_N+1, true> reduced_out = bigint_sub<_N+1>(adder_out, q);

    // Use reduced_out only if non-negative
    return (!reduced_out[_N]) ? (ac_int<_N, false>)reduced_out : 
                               (ac_int<_N, false>)adder_out;
}

#endif /* _MODADD_H_ */
