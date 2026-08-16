#ifndef _L0_INT_ADD_H_
#define _L0_INT_ADD_H_

#include <ac_int.h>
#include "params.h"

template<int _BITWIDTH>
class l0_int_add_impl {
public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<_BITWIDTH+1, false> &z
    ) {
        z = x + y;
    }
};

#endif /* _L0_INT_ADD_H_ */
