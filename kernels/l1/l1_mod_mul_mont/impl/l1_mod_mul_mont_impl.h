#ifndef _L1_MOD_MUL_MONT_H_
#define _L1_MOD_MUL_MONT_H_

#include <ac_int.h>
#include "params.h"

template<int _BITWIDTH>
class l1_mod_mul_mont_impl {
public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<_BITWIDTH+1, false> &z
    ) {
        // TODO: Implement kernel
    }
};

#endif /* _L1_MOD_MUL_MONT_H_ */
