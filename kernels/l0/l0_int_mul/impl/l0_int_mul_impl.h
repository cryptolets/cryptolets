#ifndef _L0_INT_MUL_H_
#define _L0_INT_MUL_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_sb.h"
#include "l0_int_mul_kar.h"

// A truncated output leaves the tools free to drop whatever only fed the
// bits that were cut, which is most of one half for a schoolbook multiply.
template<int _BITWIDTH,
         int _MUL_OUTPUT_TYPE = MUL_OUTPUT_FULL,
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
        ac_int<2*_BITWIDTH, false> full_output;
        if constexpr (_MUL_TYPE == MUL_KAR) {
            full_output = l0_int_mul_kar<_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH,_BITWIDTH>(x, y);
        } else if constexpr (_MUL_TYPE == MUL_SB) {
            full_output = l0_int_mul_sb<_BASE_MUL_WIDTH,_BITWIDTH>(x, y);
        } else { // MUL_NOR
            full_output = x * y;
        }

        if constexpr (_MUL_OUTPUT_TYPE == MUL_OUTPUT_FULL) {
            z = full_output;
        } else if constexpr (_MUL_OUTPUT_TYPE == MUL_OUTPUT_LO) {
            z = full_output.template slc<_BITWIDTH>(0);
        } else { // MUL_OUTPUT_HI
            z = full_output.template slc<_BITWIDTH>(_BITWIDTH);
        }
    }
};

#endif /* _L0_INT_MUL_H_ */
