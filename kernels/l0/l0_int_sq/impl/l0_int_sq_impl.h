#ifndef _L0_INT_SQ_H_
#define _L0_INT_SQ_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"
#include "l0_int_mul_sb.h"
#include "l0_int_mul_kar.h"

// Squaring combined with Karatsuba Decomposition
template<int _BITWIDTH, int _MUL_TYPE, int _BASE_MUL_WIDTH, int _KAR_BASE_MUL_WIDTH>
ac_int<2*_BITWIDTH, false> l0_int_sq_gen(
    const ac_int<_BITWIDTH, false> x
) {
    if constexpr (_MUL_TYPE == MUL_KAR && _BITWIDTH > (_KAR_BASE_MUL_WIDTH+2)) {
        // asymmetric split
        static constexpr int L = _BITWIDTH / 2;     // floor
        static constexpr int H = _BITWIDTH - L;     // ceil

        ac_int<L,false> x0 = x.template slc<L>(0);
        ac_int<H,false> x1 = x.template slc<H>(L);

        // recursive terms
        ac_int<2*L,false> z0 = l0_int_sq_gen<L,_MUL_TYPE,_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH>(x0);
        ac_int<2*H,false> z2 = l0_int_sq_gen<H,_MUL_TYPE,_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH>(x1);
        ac_int<L+H,false> z1;

        // Karatsuba doesn't work for different bitwidths, so use schoolbook instead
        if constexpr (L == H) {
            z1 = l0_int_mul_kar<_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH,L>(x0, x1);
        } else {
            z1 = l0_int_mul_sb<_BASE_MUL_WIDTH,L,H>(x0, x1);
        }

        // combine
        ac_int<2*_BITWIDTH,false> z0_ext = z0;
        ac_int<2*_BITWIDTH,false> z1_ext = (ac_int<2*_BITWIDTH,false>)z1 << L;      // shift by low part
        ac_int<2*_BITWIDTH,false> z2_ext = (ac_int<2*_BITWIDTH,false>)z2 << (2*L);  // shift by 2*low part

        return z2_ext + (z1_ext << 1) + z0_ext;  // multiply cross term by 2

    } else if constexpr (_MUL_TYPE == MUL_NOR) {
        return x * x;

    } else { // schoolbook, and karatsuba at its base case
        return l0_int_mul_sb<_BASE_MUL_WIDTH,_BITWIDTH,_BITWIDTH>(x, x);
    }
}

template<int _BITWIDTH,
         int _MUL_TYPE = MUL_TYPE,
         int _BASE_MUL_WIDTH = BASE_MUL_WIDTH,
         int _KAR_BASE_MUL_WIDTH = KAR_BASE_MUL_WIDTH>
class l0_int_sq_impl {
    l0_int_mul_impl<_BITWIDTH, _MUL_TYPE, _BASE_MUL_WIDTH, _KAR_BASE_MUL_WIDTH> int_mul_inst;

public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        ac_int<2*_BITWIDTH, false> &z
    ) {
        z = l0_int_sq_gen<_BITWIDTH,_MUL_TYPE,_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH>(x);
    }
};

#endif /* _L0_INT_SQ_H_ */
