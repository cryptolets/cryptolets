#ifndef _L0_INT_CMUL_H_
#define _L0_INT_CMUL_H_

#include <ac_int.h>
#include "params.h"

// Constant multiplier (cmul) for a given constant

template<int _BITWIDTH,
         class _CMUL_CONST,
         int _CMUL_OUTPUT_TYPE=CMUL_OUTPUT_FULL>
struct l0_int_cmul_consts {
    static constexpr int OUT_FULL = _BITWIDTH + _CMUL_CONST::W;

    // Derive output width based on the output type at compile time
    static constexpr int OUT_WIDTH =
        (_CMUL_OUTPUT_TYPE == CMUL_OUTPUT_FULL) ? OUT_FULL :
        (_CMUL_OUTPUT_TYPE == CMUL_OUTPUT_LO)   ? _CMUL_CONST::W :
                                                  OUT_FULL - _BITWIDTH;
};

template<int _BITWIDTH, 
         class _CMUL_CONST, 
         int _CMUL_OUTPUT_TYPE=CMUL_OUTPUT_FULL>
class l0_int_cmul_impl {
public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        ac_int<l0_int_cmul_consts<_BITWIDTH, _CMUL_CONST, _CMUL_OUTPUT_TYPE>::OUT_WIDTH, false> &z
    ) {
        if constexpr (_CMUL_OUTPUT_TYPE == CMUL_OUTPUT_FULL) {
            z = x * _CMUL_CONST::VALUE(); // full product
        } else if constexpr (_CMUL_OUTPUT_TYPE == CMUL_OUTPUT_LO) {
            // lower half of the product
            z = (x * _CMUL_CONST::VALUE()).template slc<l0_int_cmul_consts<_BITWIDTH, _CMUL_CONST, _CMUL_OUTPUT_TYPE>::OUT_WIDTH>(0);
        } else {
            // upper half of the product
            z = (x * _CMUL_CONST::VALUE()).template slc<l0_int_cmul_consts<_BITWIDTH, _CMUL_CONST, _CMUL_OUTPUT_TYPE>::OUT_WIDTH>(_BITWIDTH);
        }
    }
};

#endif /* _L0_INT_CMUL_H_ */
