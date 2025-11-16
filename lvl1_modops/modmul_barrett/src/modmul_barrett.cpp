#include "modmul_barrett.h"

// Barrett Reduction helper function
wide_t barrett_reduction(wide_2x_t t, const wide_t q, const wide_2x_t mu) {

#if REDC_TYPE == FIXED_RC
    wide_t m_red = cmul_mu(t);
#else
    wide_t m_red = mul_red_gen<2*BITWIDTH, 1>(t, mu).slc<BITWIDTH>(2 * BITWIDTH);
#endif

#if Q_TYPE == FIXED_Q 
    wide_2x_t mq = cmul_q(m_red);
#else
    wide_2x_t mq = mul_f(m_red, q);
#endif

    wide_2x_signed_t t_mq = t - mq;
    wide_2_t diff = t_mq.slc<BITWIDTH+2>(0);

    wide_2_signed_t path1 = diff - 2*q;
    wide_signed_t path2 = diff - q;
    wide_t path3 = (wide_t)diff;
    
    return (!path1[BITWIDTH + 1]) ? (wide_t)path1
            : (!path2[BITWIDTH]) ? (wide_t)path2
            : path3;
}

// Private helpers
#if PREC_TYPE == SINGLE_PREC

wide_t modmul_barrett_core(const wide_t x, const wide_t y, const wide_t q, const wide_2x_t mu) {
    wide_2x_t t = mul_f(x, y);
    return barrett_reduction(t, q, mu);
}

wide_t modsq_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu) {
    wide_2x_t t = sq_f(x);
    return barrett_reduction(t, q, mu);
}

// special case where we are multiplying by a const
#ifdef FIELD_A_HEX
    wide_t cmodmul_a_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu) {
        wide_2x_t t = cmul_field_a(x); // compile to constant multiplier
        return barrett_reduction(t, q, mu);
    }
#endif

#ifdef FIELD_D_HEX
    wide_t cmodmul_d_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu) {
        wide_2x_t t = cmul_field_d(x); // compile to constant multiplier
        return barrett_reduction(t, q, mu);
    }
#endif

#ifdef FIELD_K_HEX
    wide_t cmodmul_k_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu) {
        wide_2x_t t = cmul_field_k(x); // compile to constant multiplier
        return barrett_reduction(t, q, mu);
    }
#endif

#elif PREC_TYPE == MULTI_PREC

// wide_t modmul_barrett_core(const wide_t x, const wide_t y, const wide_t q, const wide_2x_t mu) {
//     return 0;
// }
wide_t modmul_barrett_core(const wide_t x, const wide_t y, const wide_t m, const wide_2x_t mu) {
    // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
    // 14.42 Algorithm Barrett modular reduction

    // Assume: LIMBS = k, WBW = b, wide_t = k*WBW bits, wide_2x_t = 2*k*WBW bits
    wide_2x_t t = mul_f(x, y);

    // 1. q1 = floor(x / b^{k-1})
    ac_int<2*LIMBS*WBW, false> x_full = t;
    ac_int<LIMBS*WBW+1, false> q1 = x_full >> (WBW * (LIMBS - 1));

    // 1. q2 = q1 * mu
    ac_int<2*LIMBS*WBW+2, false> q2 = (ac_int<2*LIMBS*WBW+2, false>)mul_f_gen<LIMBS*WBW+1, 2*LIMBS*WBW>(q1, mu);

    // 1. q3 = floor(q2 / b^{k+1})
    ac_int<2*LIMBS*WBW+2, false> q2_full = q2;
    ac_int<LIMBS*WBW+1, false> q3 = q2_full >> (WBW * (LIMBS + 1));

    // 2. r1 = x mod b^{k+1}
    ac_int<(LIMBS+1)*WBW, false> r1 = x_full.slc<(LIMBS+1)*WBW>(0);

    // 2. r2 = (q3 * m) mod b^{k+1}
    ac_int<2*(LIMBS+1)*WBW, false> q3m = (ac_int<2*(LIMBS+1)*WBW, false>)mul_f_gen<LIMBS*WBW+1, LIMBS*WBW>(q3, m);
    ac_int<(LIMBS+1)*WBW, false> r2 = q3m.slc<(LIMBS+1)*WBW>(0);

    // 2. r = r1 - r2
    ac_int<(LIMBS+1)*WBW+1, true> r = r1 - r2;

    // 3. If r < 0 then r = r + b^{k+1}
    if (r < 0)
        r += ac_int<(LIMBS+1)*WBW+1, true>(1) << ((LIMBS+1)*WBW);

    // 4. While r >= m do: r = r - m
    ac_int<LIMBS*WBW, false> m_full = m;
    while (r >= m_full)
        r -= m_full;

    // 5. Return r as wide_t
    return (wide_t)r;
}

wide_t modsq_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu) {
    return modmul_barrett_core(x, x, q, mu);
}

#endif

// Public API
wide_t modmul_barrett(
    const wide_t x, const wide_t y
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_2x_t mu
#endif
) {

#if Q_TYPE == FIXED_Q
    const wide_t q = Q;
#endif 

#if REDC_TYPE == FIXED_RC
    const wide_2x_t mu = MU;
#endif

#ifdef MUL_SQ
    #if MUL_SQ == 1
        return modsq_barrett_core(x, q, mu);
    #else
        return modmul_barrett_core(x, y, q, mu);
    #endif
#else
    return modmul_barrett_core(x, y, q, mu);
#endif
}

wide_t modsq_barrett(
    const wide_t x
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_2x_t mu
#endif
) {

#if Q_TYPE == FIXED_Q
    const wide_t q = Q;
#endif 

#if REDC_TYPE == FIXED_RC
    const wide_2x_t mu = MU;
#endif

    return modsq_barrett_core(x, q, mu);
}
