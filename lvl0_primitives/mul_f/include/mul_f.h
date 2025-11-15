#ifndef _MUL_F_H_
#define _MUL_F_H_

#include "primitives.h"
#include "mul_schoolbook.h"
#include "mul_karatsuba.h"

template<int BW_A, int BW_B=BW_A>
ac_int<BW_A+BW_B, false> mul_f_gen(
    const ac_int<BW_A, false> a,
    const ac_int<BW_B, false> b
) {
#if MUL_TYPE == MUL_KARATSUBA
    static_assert(BW_A == BW_B, "Karatsuba multiplier requires BW_A == BW_B");
    return mul_karatsuba_gen<BW_A>(a, b);
#elif MUL_TYPE == MUL_SCHOOLBOOK
    return mul_schoolbook_gen<BW_A, BW_B>(a, b);
#else // MUL_TYPE == MUL_NORMAL
    return a * b;
#endif
}

// for optimized variable constant reduction var mul in modmul barrett
template<int BW, int SKIP_UPPER=0>
ac_int<2*BW, false> mul_red_gen(
    const ac_int<BW, false> a,
    const ac_int<BW, false> b
) {
    static constexpr int l = BW / 2;
    static constexpr int h = BW - l;

    ac_int<l,false> a0 = a.template slc<l>(0);
    ac_int<h,false> a1 = a.template slc<h>(l);
    ac_int<l,false> b0 = b.template slc<l>(0);
    ac_int<h,false> b1 = b.template slc<h>(l);

    ac_int<l+l, false> z0 = 0;
    ac_int<h+h, false> z3 = 0;

    // recursive partial products
    if constexpr (SKIP_UPPER == 0)
        z0 = mul_f_gen<l,l>(a0, b0);

    auto z1 = mul_f_gen<l,h>(a0, b1);
    auto z2 = mul_f_gen<h,l>(a1, b0);
    
    if constexpr (SKIP_UPPER == 1)
        z3 = mul_f_gen<h,h>(a1, b1);

    // recombine
    ac_int<2*BW,false> res = 0;
    res += (ac_int<2*BW,false>) z0;
    res += ((ac_int<2*BW,false>) z1) << l;
    res += ((ac_int<2*BW,false>) z2) << l;
    res += ((ac_int<2*BW,false>) z3) << (l+l);
    return res;
}

wide_2x_t mul_f(
    const wide_t x,
    const wide_t y
);

#endif /* _MUL_F_H_ */
