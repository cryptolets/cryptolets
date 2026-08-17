#ifndef _L2_POINT_ADD_H_
#define _L2_POINT_ADD_H_

#include <ac_int.h>
#include "params.h"

template<int _BITWIDTH>
class l2_point_add_impl {
public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<_BITWIDTH+1, false> &z
    ) {
        // TODO: Implement kernel
    }
};

#endif /* _L2_POINT_ADD_H_ */
