#ifndef _L1_MOD_ADD_H_
#define _L1_MOD_ADD_H_

#include <ac_int.h>
#include "params.h"
#include "l0_add.h"
#include "l0_sub.h"
#include "l1_mod_add_mw.h"

template<int _N, bool _MULTI_WORD = false, int _BASE = 32>
ac_int<_N, false> l1_mod_add(
    const ac_int<_N, false> a,
    const ac_int<_N, false> b,
    const ac_int<_N, false> q
) {
    if constexpr (!_MULTI_WORD) {
        ac_int<_N+1, false> adder_out = l0_add<_N>(a, b);
        ac_int<_N+1, true> reduced_out = l0_sub<_N+1>(adder_out, q);

        // Use reduced_out only if non-negative
        return (!reduced_out[_N]) ? (ac_int<_N, false>)reduced_out :
                                   (ac_int<_N, false>)adder_out;
    } else {
        return l1_mod_add_mw<_N, _BASE>(a, b, q);
    }
}

#endif /* _L1_MOD_ADD_H_ */
