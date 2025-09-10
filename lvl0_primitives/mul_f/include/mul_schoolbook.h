#ifndef _MUL_SCHOOLBOOK_H_
#define _MUL_SCHOOLBOOK_H_

#include "primitives.h"

// Recursive schoolbook multiplier for arbitrary BW
// Works for odd and even bitwidths
#if CCORE_MULS == 1
#pragma hls_design ccore
#endif
template<int BW_A, int BW_B=BW_A>
ac_int<BW_A+BW_B,false> mul_schoolbook_gen(
    const ac_int<BW_A,false> a,
    const ac_int<BW_B,false> b
) {
    // +1 ensures karatsuba uneven bitwidths don't result in an extra level
    if constexpr ((BW_A <= (BASE_MUL_WIDTH+2)) && (BW_B <= (BASE_MUL_WIDTH+2))) {
        return a * b;
    } else {
        // split a
        static constexpr int la = BW_A / 2;
        static constexpr int ha = BW_A - la;

        ac_int<la,false> a0 = a.template slc<la>(0);
        ac_int<ha,false> a1 = a.template slc<ha>(la);

        // split b
        static constexpr int lb = BW_B / 2;
        static constexpr int hb = BW_B - lb;

        ac_int<lb,false> b0 = b.template slc<lb>(0);
        ac_int<hb,false> b1 = b.template slc<hb>(lb);

        // recursive partial products
        auto z0 = mul_schoolbook_gen<la,lb>(a0, b0);
        auto z1 = mul_schoolbook_gen<la,hb>(a0, b1);
        auto z2 = mul_schoolbook_gen<ha,lb>(a1, b0);
        auto z3 = mul_schoolbook_gen<ha,hb>(a1, b1);

        // recombine
        ac_int<BW_A+BW_B,false> res = 0;
        res += (ac_int<BW_A+BW_B,false>) z0;
        res += ((ac_int<BW_A+BW_B,false>) z1) << lb;
        res += ((ac_int<BW_A+BW_B,false>) z2) << la;
        res += ((ac_int<BW_A+BW_B,false>) z3) << (la+lb);

        return res;
    }
}

#endif // _MUL_SCHOOLBOOK_H_
