#include "modmul_mont.h"

// Private helpers
#if PRECISION_MODE == PREC_SINGLE

wide_t modmul_mont_core(const wide_t x, const wide_t y, const wide_t q, const wide_t q_prime) {
    wide_2x_t t = mul_f(x, y);
    wide_t t_red = t.slc<BITWIDTH>(0);      // t & (R-1)

    // (t_red * q_prime) & (R-1)
#if Q_TYPE == FIXED_Q 
    wide_t m_red = cmul_f(t_red);
#else
    wide_t m_red = mul_f(t_red, q_prime);
#endif

    wide_2x_t mq = mul_f(m_red, q);
    wide_2x_1_t t_mq = t + mq;
    wide_t u = t_mq >> BITWIDTH;
    wide_signed_t diff = u - q;
    return (!diff[BITWIDTH]) ? (wide_t)diff : u;
}

wide_t modsq_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
    wide_2x_t t = sq_f(x);
    wide_t t_red = t.slc<BITWIDTH>(0);      // t & (R-1)

    // (t_red * q_prime) & (R-1)
#if Q_TYPE == FIXED_Q 
    wide_t m_red = cmul_f(t_red);
#else
    wide_t m_red = mul_f(t_red, q_prime);
#endif

    wide_2x_t mq = mul_f(m_red, q);
    wide_2x_1_t t_mq = t + mq;
    wide_t u = t_mq >> BITWIDTH;
    wide_signed_t diff = u - q;
    return (!diff[BITWIDTH]) ? (wide_t)diff : u;
}

#else // PREC_MULTI

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

        // TODO: we can do const mul + reduce optimization here
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

// TODO:
wide_t modsq_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
    return modmul_mont_core(x, x, q, q_prime);
}

#endif

// Public API (fixed-q wrappers)
#if Q_TYPE == FIXED_Q
wide_t modmul_mont(const wide_t x, const wide_t y) {
    return modmul_mont_core(x, y, Q, Q_PRIME);
}

wide_t modsq_mont(const wide_t x) {
    return modsq_mont_core(x, Q, Q_PRIME);
}

#else

// Public API (variable-q)
wide_t modmul_mont(const wide_t x, const wide_t y,
                   const wide_t q, const wide_t q_prime) {
    return modmul_mont_core(x, y, q, q_prime);
}

wide_t modsq_mont(const wide_t x,
                  const wide_t q, const wide_t q_prime) {
    return modsq_mont_core(x, q, q_prime);
}

#endif
