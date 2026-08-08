#ifndef _L0_ADD_H_
#define _L0_ADD_H_

#include <ac_int.h>
#include "params.h"
#include "l0_add_mw.h"

template<int _N, bool _MULTI_WORD = false, int _BASE = 32>
ac_int<_N+1, false> l0_add(
    const ac_int<_N, false> x,
    const ac_int<_N, false> y
) {
    if constexpr (!_MULTI_WORD) {
        return x + y;
    } else {
        return l0_add_mw<_N, _BASE>(x, y);
    }
}

#endif /* _L0_ADD_H_ */
