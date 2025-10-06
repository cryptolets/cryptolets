#include "sub_f.h"

#if PREC_TYPE == SINGLE_PREC

wide_signed_t sub_f(
    const wide_t a,
    const wide_t b
) {
    return a - b;
}

#elif PREC_TYPE == MULTI_PREC

wide_signed_t sub_f(
    const wide_t x,
    const wide_t y
) {
    // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
    // 14.9 Algorithm Multiple-precision subtraction
    // Note: LIMBS = n+1, WBW = b

    wide_signed_t w;
    ac_int<1, true> c = 0; // c <- 0

    for (int i = 0; i < LIMBS; i++) {
        // 2.1 w_i <- (x_i + y_i - c) mod b
        word_signed_t w_i_ext = x.slc<WBW>(i * WBW) - y.slc<WBW>(i * WBW) + c;
        w.set_slc(i*WBW, w_i_ext.slc<WBW>(0));

        // Note: same logic more hardware friendly
        // 2.2 If (x_i - y_i + c) >= 0 then c <- 0; otherwise c <- -1
        c = w_i_ext[WBW];
    }
    
    w[BITWIDTH] = c;
    return w; // 3.
}

#endif