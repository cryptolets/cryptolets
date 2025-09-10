#include "add_f.h"

#if PRECISION_MODE == PREC_SINGLE

wide_1_t add_f(
    const wide_t x,
    const wide_t y
) {
    return x + y;
}

#else // PREC_MULTI

wide_1_t add_f(
    const wide_t x,
    const wide_t y
) {
    // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
    // 14.7 Algorithm Multiple-precision addition
    // Note: LIMBS = n+1, WBW = b

    wide_1_t w;
    ac_int<1, false> c = 0; // c <- 0

    // 2.
    for (int i = 0; i < LIMBS; i++) {
        // 2.1 w_i <- (x_i + y_i + c) mod b
        word_1_t w_i_ext = x.slc<WBW>(i * WBW) + y.slc<WBW>(i * WBW) + c;
        w.set_slc(i*WBW, w_i_ext.slc<WBW>(0));

        // Note: same logic more hardware friendly
        // 2.2 If (x_i + y_i + c) < b then c <- 0; otherwise c <- 1
        c = w_i_ext[WBW];
    }

    w[BITWIDTH] = c; // 3. w_(n+1) <- c
    return w; // 4.
}


#endif