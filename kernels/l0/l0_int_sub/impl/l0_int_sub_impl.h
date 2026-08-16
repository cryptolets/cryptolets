#ifndef _L0_INT_SUB_H_
#define _L0_INT_SUB_H_

#include <ac_int.h>
#include "params.h"

template<int _BITWIDTH>
class l0_int_sub_impl {
public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<_BITWIDTH+1, true> &z
    ) {
        z = x - y;
    }
};

#endif /* _L0_INT_SUB_H_ */
