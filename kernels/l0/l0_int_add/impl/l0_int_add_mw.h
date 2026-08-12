#ifndef _L0_INT_ADD_MW_H_
#define _L0_INT_ADD_MW_H_

#include <ac_int.h>
#include "params.h"

// https://cacr.uwaterloo.ca/hac/about/chap14.pdf
// 14.7 Algorithm Multiple-precision addition
// Note: DIGITS = n+1, _WORD_WIDTH = b (variable name mapping to reference)

template<int _BITWIDTH, int _WORD_WIDTH>
ac_int<_BITWIDTH+1, false> l0_int_add_mw_impl(
    const ac_int<_BITWIDTH, false> x,
    const ac_int<_BITWIDTH, false> y
) {
    static_assert(_BITWIDTH % _WORD_WIDTH == 0, "BITWIDTH must be divisible by WORD_WIDTH");
    static constexpr int DIGITS = _BITWIDTH / _WORD_WIDTH;

    ac_int<_BITWIDTH+1, false> w;
    ac_int<1, false> c = 0; // c <- 0

    // 2.
    for (int i = 0; i < DIGITS; i++) {
        // 2.1 w_i <- (x_i + y_i + c) mod b
        ac_int<_WORD_WIDTH+1, false> w_i_ext = x.slc<_WORD_WIDTH>(i * _WORD_WIDTH) + y.slc<_WORD_WIDTH>(i * _WORD_WIDTH) + c;
        w.set_slc(i*_WORD_WIDTH, w_i_ext.slc<_WORD_WIDTH>(0));

        // Note: same logic more hardware friendly
        // 2.2 If (x_i + y_i + c) < b then c <- 0; otherwise c <- 1
        c = w_i_ext[_WORD_WIDTH];
    }

    w[_BITWIDTH] = c; // 3. w_(n+1) <- c
    return w; // 4.
}

#endif /* _L0_INT_ADD_MW_H_ */
