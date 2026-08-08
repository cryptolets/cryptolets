#ifndef _L0_SUB_H_
#define _L0_SUB_H_

#include <ac_int.h>
#include "params.h"

template<int _N>
ac_int<_N+1, false> l0_sub(
    const ac_int<_N, false> x,
    const ac_int<_N, false> y
) {
   return x - y;
}

#endif /* _L0_SUB_H_ */
