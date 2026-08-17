#ifndef _L0_INT_CMUL_H_
#define _L0_INT_CMUL_H_

#include <ac_int.h>
#include "params.h"

template<int _BITWIDTH>
class l0_int_cmul_impl {
public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<_BITWIDTH+1, false> &z
    ) {
        // TODO: Implement kernel
    }
};

#endif /* _L0_INT_CMUL_H_ */
