#include "modadd.h"

// Core implementation (shared by both fixed and variable Q)

#if PRECISION_MODE == PREC_SINGLE

wide_t modadd_core(const wide_t a, const wide_t b, const wide_t q) {
    wide_1_t adder_out = a + b;
    wide_signed_t reduced_out = adder_out - q;

    // Use reduced_out only if non-negative
    return (!reduced_out[BITWIDTH]) ? (wide_t)reduced_out : (wide_t)adder_out;
}

wide_t moddouble_core(const wide_t a, const wide_t q) {
    wide_1_t adder_out = wide_1_t(a) << 1;
    wide_signed_t reduced_out = adder_out - q;

    // Use reduced_out only if non-negative
    return (!reduced_out[BITWIDTH]) ? (wide_t)reduced_out : (wide_t)adder_out;
}

#else // PREC_MULTI

wide_t modadd_core(
    const wide_t a, 
    const wide_t b, 
    const wide_t q
) {
    // using algorithms implemented in mp_add and mp_sub kernels
    wide_t adder_out;
    ac_int<1, false> c_0 = 0;

    wide_t reduced_out;
    ac_int<1, true> c_1 = 0;
    
    // Use one loop to ensure word level ops overlap
    for (int i = 0; i < LIMBS; i++) {
        // 1. adder_out = a + b;
        word_1_t w_i_ext_0 = a.slc<WBW>(i * WBW) + b.slc<WBW>(i * WBW) + c_0;
        adder_out.set_slc(i*WBW, w_i_ext_0.slc<WBW>(0));
        c_0 = w_i_ext_0[WBW];

        // 2. reduced_out = adder_out - q;
        word_signed_t w_i_ext_1 = adder_out.slc<WBW>(i * WBW) - q.slc<WBW>(i * WBW) + c_1;
        reduced_out.set_slc(i*WBW, w_i_ext_1.slc<WBW>(0));
        c_1 = w_i_ext_1[WBW];
    }

    wide_t result;
    // 3. if !c_1 then reduced_out else adder_out;
    for (int i = 0; i < LIMBS; i++) {        
        word_t reduced_out_w = reduced_out.slc<WBW>(i * WBW);
        word_t adder_out_w = adder_out.slc<WBW>(i * WBW);
        word_t r_w = !c_1 ? reduced_out_w : adder_out_w;
        result.set_slc(i * WBW, r_w);
    }

    return result;
}

// TODO:
wide_t moddouble_core(const wide_t a, const wide_t q) {
    return modadd_core(a, a, q);
}

#endif

#if Q_TYPE == FIXED_Q

wide_t modadd(const wide_t a, const wide_t b) {
    return modadd_core(a, b, Q);
}

wide_t moddouble(const wide_t a) {
    return moddouble_core(a, Q);
}

#else // VAR_Q

wide_t modadd(const wide_t a, const wide_t b, const wide_t q) {
    return modadd_core(a, b, q);
}

wide_t moddouble(const wide_t a, const wide_t q) {
    return moddouble_core(a, q);
}

#endif
