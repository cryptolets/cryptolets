#include "modmul_barrett.h"

// Barrett Reduction helper function
wide_t barrett_reduction(wide_2x_t t, const wide_t q, const wide_2x_t mu) {

#if REDC_TYPE == FIXED_RC
    wide_t m_red = cmul_mu(t);
#else
    wide_t m_red = mul_f_gen<2*BITWIDTH>(t, mu).slc<BITWIDTH>(2 * BITWIDTH);
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

wide_t modmul_barrett_core(const wide_t x, const wide_t y, const wide_t q, const wide_2x_t mu) {
    return 0;
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

    return modmul_barrett_core(x, y, q, mu);
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
