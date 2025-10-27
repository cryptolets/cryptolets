#ifndef _CMUL_F_H_
#define _CMUL_F_H_

#include "primitives.h"

// NAF based implementation
template<int BW, int CONST_NAF_LEN>
ac_int<2*BW> cmul_f_naf_gen(const ac_int<BW> a, const int CONST_NAF[CONST_NAF_LEN]) {
    static ac_int<2*BW, false> adds[CONST_NAF_LEN];
    static ac_int<2*BW, false> subs[CONST_NAF_LEN];

    #pragma hls_unroll yes
    for (int i = 0; i < CONST_NAF_LEN; ++i) {
        adds[i] = (CONST_NAF[i] == 1) ? (ac_int<2*BW, false>)a << i : 0;
        subs[i] = (CONST_NAF[i] == -1) ? (ac_int<2*BW, false>)a << i : 0;
    }

    ac_int<2*BW, false> acc = 0;
    #pragma hls_unroll yes
    for (int i = 0; i < CONST_NAF_LEN; ++i)
        acc += adds[i];

    #pragma hls_unroll yes
    for (int i = 0; i < CONST_NAF_LEN; ++i)
        acc -= subs[i];

    return acc;
}

// regular shift add const multiplier
template<int BW>
ac_int<2*BW> cmul_f_sa_gen(const ac_int<BW> a, const ac_int<BW> CONST) {
    static ac_int<2*BW, false> sum[BITWIDTH];

    #pragma hls_unroll yes
    for (int i = 0; i < BITWIDTH; ++i) {
        if (CONST[i] == 1)
            sum[i] = (ac_int<2*BW, false>)a << i;
        else
            sum[i] = 0;
    }

    ac_int<2*BW, false> acc = 0;
    #pragma hls_unroll yes
    for (int i = 0; i < BITWIDTH; ++i)
        acc += sum[i];

    return acc;
}

// Wrapper function for selection
template<int BW, int CONST_NAF_LEN>
ac_int<2*BW> cmul_f_gen(
    const ac_int<BW> a, 
    const ac_int<BW> CONST,
    const int CONST_NAF[CONST_NAF_LEN]
) {
#if CMUL_TYPE == CMUL_NAF
    return cmul_f_naf_gen<BW, CONST_NAF_LEN>(a, CONST_NAF);
#elif CMUL_TYPE == CMUL_SA
    return cmul_f_sa_gen<BW>(a, CONST);
#else // CMUL_NORMAL
    return a * CONST;
#endif
}

wide_t cmul_f(const wide_t a);

// -- For heigher level use --
// For modmul constant multiplications
wide_t cmul_q_prime(const wide_t x);
wide_2x_t cmul_q(const wide_t x);
wide_t cmul_mu(const wide_2x_t x);

// For field constant multiplications in montgomery domain
wide_2x_t cmul_field_a_mont(const wide_2x_t x);
wide_2x_t cmul_field_d_mont(const wide_2x_t x);
wide_2x_t cmul_field_k_mont(const wide_2x_t x);

// For field constant multiplications in normal domain (for barrett)
wide_2x_t cmul_field_a(const wide_2x_t x);
wide_2x_t cmul_field_d(const wide_2x_t x);
wide_2x_t cmul_field_k(const wide_2x_t x);

#endif /* _CMUL_F_H_ */
