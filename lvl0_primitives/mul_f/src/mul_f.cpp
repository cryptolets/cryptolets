#include "mul_f.h"

#if PRECISION_MODE == PREC_SINGLE

wide_2x_t mul_f(
    const wide_t x,
    const wide_t y
) {
    return mul_f_gen<BITWIDTH>(x, y);
}

#else // PREC_MULTI

wide_2x_t mul_f(
    const wide_t x,
    const wide_t y
) {
    // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
    // 14.12 Algorithm Multiple-precision multiplication
    // Note: LIMBS = n+1, WBW = b
    
    wide_2x_t w = 0; // 1. zero out

    // 2.
    for (int i=0; i<LIMBS; i++) {
        word_t c = 0; // c <- 0
        for (int j=0; j<LIMBS; j++) {
            word_2x_t prod = mul_f_gen<WBW>(x.slc<WBW>(j*WBW), y.slc<WBW>(i*WBW)); // x_j * y_j
            word_t w_i_j = w.slc<WBW>((i+j)*WBW); // get w_(i+j)
            word_2x_t uv = w_i_j + prod + c; // (uv)_b = w_(i+j) + (x_j) * (y_i) + c
            w.set_slc((i+j)*WBW, uv.slc<WBW>(0)); // set w_(i+j) <- v
            c = uv.slc<WBW>(WBW); // set c <- u
        }
        w.set_slc((i+LIMBS)*WBW, c); // w_(i+n+1)
    }
    
    return w; // 3.
}

#endif
