#ifndef _L0_INT_MUL_H_
#define _L0_INT_MUL_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_sb.h"
#include "l0_int_mul_kar.h"

template<int _BITWIDTH,
         int _MUL_TYPE = MUL_TYPE,
         int _BASE_MUL_WIDTH = BASE_MUL_WIDTH,
         int _KAR_BASE_MUL_WIDTH = KAR_BASE_MUL_WIDTH>
class l0_int_mul_impl {
public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<2*_BITWIDTH, false> &z
    ) {
        if constexpr (_MUL_TYPE == MUL_KAR) {
            z = l0_int_mul_kar<_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH,_BITWIDTH>(x, y);
        } else if constexpr (_MUL_TYPE == MUL_SB) {
            z = l0_int_mul_sb<_BASE_MUL_WIDTH,_BITWIDTH>(x, y);
        } else { // MUL_NOR
            z = x * y;
        }
    }
};

#endif /* _L0_INT_MUL_H_ */
