#ifndef _CMUL_F_H_
#define _CMUL_F_H_

#include "primitives.h"

// NAF based implementation
template<int BW, int CONST_NAF_LEN>
ac_int<2*BW, false> cmul_f_naf_gen(
    const ac_int<BW, false> a, 
    const int CONST_NAF[CONST_NAF_LEN]
) {
    ac_int<2*BW, false> adds[CONST_NAF_LEN];
    ac_int<2*BW, false> subs[CONST_NAF_LEN];

    #pragma hls_unroll yes
    for (int i = 0; i < CONST_NAF_LEN; ++i) {
        adds[i] = (CONST_NAF[i] == 1) ? (ac_int<2*BW, false>)a << i : 0;
        subs[i] = (CONST_NAF[i] == -1) ? (ac_int<2*BW, false>)a << i : 0;
    }

    ac_int<2*BW, false> acc = 0;
    #pragma hls_unroll yes
    for (int i = 0; i < (2*CONST_NAF_LEN); ++i)
        if (i < CONST_NAF_LEN)
            acc += adds[i];
        else
            acc -= subs[i-CONST_NAF_LEN];

    return acc;
}

// regular shift add const multiplier
template<int BW>
ac_int<2*BW, false> cmul_f_sa_gen(
    const ac_int<BW, false> a, 
    const ac_int<BW, false> CONST
) {
    ac_int<2*BW, false> sum[BW];

    #pragma hls_unroll yes
    for (int i = 0; i < BW; ++i) {
        sum[i] = (CONST[i] == 1) ? (ac_int<2*BW, false>)a << i : 0;
    }

    ac_int<2*BW, false> acc = 0;
    #pragma hls_unroll yes
    for (int i = 0; i < BW; ++i)
        acc += sum[i];

    return acc;
}

// Wrapper function for selection
template<int BW, int CONST_NAF_LEN>
ac_int<2*BW, false> cmul_f_gen(
    const ac_int<BW, false> a, 
    const ac_int<BW, false> CONST,
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
wide_2x_t cmul_field_a_mont(const wide_t x);
wide_2x_t cmul_field_d_mont(const wide_t x);
wide_2x_t cmul_field_k_mont(const wide_t x);

// For field constant multiplications in normal domain (for barrett)
wide_2x_t cmul_field_a(const wide_t x);
wide_2x_t cmul_field_d(const wide_t x);
wide_2x_t cmul_field_k(const wide_t x);

#endif /* _CMUL_F_H_ */
