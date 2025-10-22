#include "modmul_mont.h"

#if PREC_TYPE == SINGLE_PREC
// Mont Reduction helper function
inline wide_t mont_reduction(wide_2x_t t, const wide_t q, const wide_t q_prime) {
    wide_t t_red = t.slc<BITWIDTH>(0);      // t & (R-1)

    // (t_red * q_prime) & (R-1)
#if REDC_TYPE == FIXED_RC
    wide_t m_red = (t_red * Q_PRIME).slc<BITWIDTH>(0); // compile to constant multiplier
#else
    wide_t m_red = mul_f(t_red, q_prime);
#endif

#if Q_TYPE == FIXED_Q
    wide_2x_t mq = m_red * Q; // compile to constant multiplier
#else
    wide_2x_t mq = mul_f(m_red, q);
#endif

    wide_2x_1_t t_mq = t + mq;
    wide_1_t u = t_mq >> BITWIDTH;
    wide_signed_t diff = u - q;
    return (!diff[BITWIDTH]) ? (wide_t)diff : (wide_t)u;
}

wide_t modmul_mont_core(const wide_t x, const wide_t y, const wide_t q, const wide_t q_prime) {
    wide_2x_t t = mul_f(x, y);
    return mont_reduction(t, q, q_prime);
}

wide_t modsq_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
    wide_2x_t t = sq_f(x);
    return mont_reduction(t, q, q_prime);
}

// special case where we are multiplying by a const
#ifdef FIELD_A_MONT_HEX
    wide_t cmodmul_a_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
        wide_2x_t t = x * FIELD_A_MONT; // compile to constant multiplier
        return mont_reduction(t, q, q_prime);
    }
#endif

#ifdef FIELD_D_MONT_HEX
    wide_t cmodmul_d_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
        wide_2x_t t = x * FIELD_D_MONT; // compile to constant multiplier
        return mont_reduction(t, q, q_prime);
    }
#endif

#ifdef FIELD_K_MONT_HEX
    wide_t cmodmul_k_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
        wide_2x_t t = x * FIELD_K_MONT; // compile to constant multiplier
        return mont_reduction(t, q, q_prime);
    }
#endif

#elif PREC_TYPE == MULTI_PREC

wide_t modmul_mont_core(const wide_t x, const wide_t y, const wide_t q, const wide_t q_prime) {
    // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
    // 14.36 Algorithm Montgomery multiplication
    // Note: LIMBS = n+1, WBW = b, q = m
    // Note: using full-width addition for simplicity, but word-width muls

    ac_int<(LIMBS+1)*WBW, false> A = 0; // 1. A <- 0
    word_t q_prime_0 = q_prime.slc<WBW>(0); // q_prime_0 = m' = -m^-1 mod b

    // 2.0
    for (int i=0; i<LIMBS; i++) {
        // 2.1 u_i <- (a_0 + x_i*y_0)*m' mod b
        // Which can also be written as:
        // u_i = (((a_0 + x_i*y_0) mod b)*m') mod b
        // axy = (a_0 + x_i*y_0) mod b

        word_t a_0 = A.slc<WBW>(0);
        word_t x_i = x.slc<WBW>(i*WBW);
        word_t y_0 = y.slc<WBW>(0);

        word_t axy = (a_0 + mul_f_gen<WBW>(x_i, y_0)).slc<WBW>(0);
        word_t u_i = mul_f_gen<WBW>(axy, q_prime_0).slc<WBW>(0); // 2.1

        // 2.2 A <- (A + x_i*y + u_i*m) / b
        ac_int<(LIMBS+1)*WBW, false> x_i_y = 0;
        ac_int<(LIMBS+1)*WBW, false> u_i_q = 0;
        
        for (int j=0; j<LIMBS; j++) {
            word_t y_j = y.slc<WBW>(j*WBW);
            auto prod1 = (ac_int<(LIMBS+1)*WBW,false>) mul_f_gen<WBW>(x_i, y_j);
            x_i_y += prod1 << (j*WBW);

            word_t q_j = q.slc<WBW>(j*WBW);
            auto prod2 = (ac_int<(LIMBS+1)*WBW,false>) mul_f_gen<WBW>(u_i, q_j);
            u_i_q += prod2 << (j*WBW);
        }

        // (A + x_i*y + u_i*m) / b
        A = (A + x_i_y + u_i_q) >> WBW;
    }

    // 3. If A >= m then A <- A - m
    ac_int<((LIMBS+1)*WBW)+1, true> A_minus_q = A - q;
    return (!A_minus_q[((LIMBS+1)*WBW)]) ? (wide_t)A_minus_q : (wide_t)A;
}

wide_t modsq_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
    return modmul_mont_core(x, x, q, q_prime);
}

#endif

// Public API
wide_t modmul_mont(
    const wide_t x, const wide_t y
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_t q_prime
#endif
) {

#if Q_TYPE == FIXED_Q
    const wide_t q = Q;
#endif 

#if REDC_TYPE == FIXED_RC
    const wide_t q_prime = Q_PRIME;
#endif

    return modmul_mont_core(x, y, q, q_prime);
}

wide_t modsq_mont(
    const wide_t x
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_t q_prime
#endif
) {

#if Q_TYPE == FIXED_Q
    const wide_t q = Q;
#endif 

#if REDC_TYPE == FIXED_RC
    const wide_t q_prime = Q_PRIME;
#endif

    return modsq_mont_core(x, q, q_prime);
}
