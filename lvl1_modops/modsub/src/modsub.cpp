#include "modsub.h"

// Core implementation (shared by both fixed and variable Q)
#if PRECISION_MODE == PREC_SINGLE

wide_t modsub_core(const wide_t a, const wide_t b, const wide_t q) {
    wide_signed_t diff = a - b;
    wide_1_t adder_out = diff + q;
    return (!diff[BITWIDTH]) ? (wide_t)diff : (wide_t)adder_out;
}

#else // PREC_MULTI

wide_t modsub_core(
    const wide_t a, 
    const wide_t b, 
    const wide_t q
) {
    // using algorithms implemented in mp_add and mp_sub kernels
    wide_t diff;
    ac_int<1, true> c_0 = 0;

    wide_t adder_out;
    ac_int<1, false> c_1 = 0;
    
    for (int i = 0; i < LIMBS; i++) {
        // 1. diff = a - b;
        word_signed_t w_i_ext_0 = a.slc<WBW>(i * WBW) - b.slc<WBW>(i * WBW) + c_0;
        diff.set_slc(i*WBW, w_i_ext_0.slc<WBW>(0));
        c_0 = w_i_ext_0[WBW];

        // 2. adder_out = diff + q;
        word_1_t w_i_ext_1 = diff.slc<WBW>(i * WBW) + q.slc<WBW>(i * WBW) + c_1;
        adder_out.set_slc(i*WBW, w_i_ext_1.slc<WBW>(0));
        c_1 = w_i_ext_1[WBW];
    }

    wide_t result;
    // 3. if !c_0 then reduced_out else adder_out;
    for (int i = 0; i < LIMBS; i++) {        
        word_t diff_w = diff.slc<WBW>(i * WBW);
        word_t adder_out_w = adder_out.slc<WBW>(i * WBW);
        word_t r_w = !c_0 ? diff_w : adder_out_w;
        result.set_slc(i * WBW, r_w);
    }

    return result;
}

#endif

#if Q_TYPE == FIXED_Q

wide_t modsub(const wide_t a, const wide_t b) {
    return modsub_core(a, b, Q);
}

#else // VAR_Q

wide_t modsub(const wide_t a, const wide_t b, const wide_t q) {
    return modsub_core(a, b, q);
}

#endif
