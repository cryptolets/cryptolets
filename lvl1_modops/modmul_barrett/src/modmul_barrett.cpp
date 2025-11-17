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

// Calculate B_EXP as the number of trailing zeros in WBW (since WBW is a power of 2)
// constexpr int B_EXP = __builtin_ctz(WBW);  // int(math.log2(WBW))
// constexpr int LIMBGROUPS = (BITWIDTH + B_EXP - 1) / B_EXP; // Equivalent to ceil(BITWIDTH / B_EXP)

#define LIMBGROUPS ((BITWIDTH + WBW - 1) / WBW)  // ceil(BITWIDTH / WBW)

// wide_t modmul_barrett_core(const wide_t x, const wide_t y, const wide_t q, const wide_2x_t mu) {
//     return 0;
// }
wide_t modmul_barrett_core(const wide_t x, const wide_t y, const wide_t m_in, const wide_2x_t mu_in) {
    // m_in is the modulus.
    // https://fractalyze.gitbook.io/intro/primitives/modular-arithmetic/modular-reduction/barrett-reduction
    // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
    // 14.42 Algorithm Barrett modular reduction
    //
    // Note: the MSB of m must not be 0. (m cannot be very small)

    // Assume: LIMBGROUPS = k, 2^WBW = b, wide_t <= k*WBW bits, wide_2x_t <= 2*k*WBW bits
    wide_2x_t t = mul_f(x, y);
    ac_int<2 * LIMBGROUPS * WBW - BITWIDTH + 1, false> mu = mu_in;
    std::cout << "t: " << t.to_string(AC_HEX) << std::endl;
    std::cout << "mu: " << mu.to_string(AC_HEX) << std::endl;

    ac_int<LIMBGROUPS * WBW, false> m = m_in;

    // 1. q1 = floor(x / b^{k-1})
    ac_int<2*LIMBGROUPS*WBW, false> x_full = t;
    ac_int<(LIMBGROUPS + 1)*WBW, false> q1 = x_full >> (WBW * (LIMBGROUPS - 1));
    std::cout << "x_full: " << x_full.to_string(AC_HEX) << std::endl;
    std::cout << "q1: " << q1.to_string(AC_HEX) << std::endl;

    // 1. q2 = q1 * mu
    // ac_int<(3*LIMBGROUPS+1)*WBW-BITWIDTH+1, false> q2 = (ac_int<(3*LIMBGROUPS+1)*WBW-BITWIDTH+1, false>)mul_f_gen<(LIMBGROUPS+1)*WBW, 2*LIMBGROUPS*WBW-BITWIDTH+1>(q1, mu);
    // 1. q2 = q1 * mu (schoolbook, WBW-bit multiplier only)
    ac_int<(3 * LIMBGROUPS + 1) * WBW - BITWIDTH + 1, false> q2 = 0;
    for (int i = 0; i < (BITWIDTH + WBW - 1) / WBW; i++) {
        ac_int<WBW, false> c = 0;
        for (int j = 0; j < (BITWIDTH + WBW - 1) / WBW; j++) {
            ac_int<WBW, false> q1_limb = q1.slc<WBW>(i * WBW);
            ac_int<WBW, false> mu_limb = mu.slc<WBW>(j * WBW);
            ac_int<2 * WBW, false> prod = mul_f_gen<WBW>(q1_limb, mu_limb);  // q1_i * mu_j

            ac_int<WBW, false> q2_ij = q2.slc<WBW>((i + j) * WBW);
            ac_int<2 * WBW, false> uv = q2_ij + prod + c;

            q2.set_slc((i + j) * WBW, uv.slc<WBW>(0));
            c = uv.slc<WBW>(WBW);
        }
        q2.set_slc((i + ((BITWIDTH + WBW - 1) / WBW)) * WBW, c);
        std::cout << "q2 (after column " << i << "): " << q2.to_string(AC_HEX) << std::endl;
    }

    std::cout << "mu: " << mu.to_string(AC_HEX) << std::endl;
    std::cout << "q2: " << q2.to_string(AC_HEX) << std::endl;

    // 1. q3 = floor(q2 / b^{k+1})
    ac_int<2*LIMBGROUPS*WBW-BITWIDTH+1, false> q3 = q2 >> (WBW * (LIMBGROUPS + 1));
    std::cout << "q3: " << q3.to_string(AC_HEX) << std::endl;

    // 2. r1 = x mod b^{k+1}
    ac_int<(LIMBGROUPS+1)*WBW, false> r1 = x_full.slc<(LIMBGROUPS+1)*WBW>(0);
    std::cout << "r1: " << r1.to_string(AC_HEX) << std::endl;

    // 2. r2 = (q3 * m) mod b^{k+1}
    // ac_int<2*LIMBGROUPS*WBW+1, false> q3m = (ac_int<2*LIMBGROUPS*WBW+1, false>)mul_f_gen<2*LIMBGROUPS*WBW-BITWIDTH+1, BITWIDTH>(q3, m);
    // 2. r2 = (q3 * m) mod b^{k+1}
    // Compute q3m = q3 * m using only WBW-bit multiplications
    ac_int<2*LIMBGROUPS*WBW+1, false> q3m = 0;
    for (int i = 0; i < LIMBGROUPS - 1; i++) {
        ac_int<WBW, false> c = 0;
        for (int j = 0; j < (BITWIDTH + WBW - 1) / WBW; j++) {
            ac_int<WBW, false> q3_limb = q3.slc<WBW>(i * WBW);
            ac_int<WBW, false> m_limb = m.slc<WBW>(j * WBW);
            ac_int<2 * WBW, false> prod = mul_f_gen<WBW>(q3_limb, m_limb);

            ac_int<WBW, false> q3m_ij = q3m.slc<WBW>((i + j) * WBW);
            ac_int<2 * WBW, false> uv = q3m_ij + prod + c;

            q3m.set_slc((i + j) * WBW, uv.slc<WBW>(0));
            c = uv.slc<WBW>(WBW);
        }
        q3m.set_slc((i + ((BITWIDTH + WBW - 1) / WBW)) * WBW, c);
    }

    ac_int<(LIMBGROUPS+1)*WBW, false> r2 = q3m.slc<(LIMBGROUPS+1)*WBW>(0);
    std::cout << "q3m: " << q3m.to_string(AC_HEX) << std::endl;
    std::cout << "r2: " << r2.to_string(AC_HEX) << std::endl;

    // 2. r = r1 - r2
    ac_int<(LIMBGROUPS+1)*WBW+1, true> r = r1 - r2;
    std::cout << "r (before correction): " << r.to_string(AC_HEX) << std::endl;

    // 3. If r < 0 then r = r + b^{k+1}
    if (r < 0){
        r += ac_int<(LIMBGROUPS+1)*WBW+1, true>(1) << ((LIMBGROUPS+1)*WBW);
        std::cout << "r (after correction): " << r.to_string(AC_HEX) << std::endl;
    }

    // 4. While r >= m do: r = r - m
    ac_int<LIMBGROUPS*WBW, false> m_full = m;
    std::cout << "m_full: " << m_full.to_string(AC_HEX) << std::endl;

    while (r >= m_full){
        r -= m_full;
        std::cout << "r (in loop): " << r.to_string(AC_HEX) << std::endl;
    }

    std::cout << "r (final): " << r.to_string(AC_HEX) << std::endl;
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
