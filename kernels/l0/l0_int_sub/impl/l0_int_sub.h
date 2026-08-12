#ifndef _L0_INT_SUB_H_
#define _L0_INT_SUB_H_

#include <ac_int.h>
#include "params.h"

template<int _BITWIDTH>
ac_int<_BITWIDTH+1, false> l0_int_sub_impl(
    const ac_int<_BITWIDTH, false> x,
    const ac_int<_BITWIDTH, false> y
) {
   return x - y;
}


#endif /* _L0_INT_SUB_H_ */
