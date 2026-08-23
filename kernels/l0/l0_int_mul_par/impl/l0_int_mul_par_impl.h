#ifndef _L0_INT_MUL_PAR_H_
#define _L0_INT_MUL_PAR_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"
#include "l0_int_mul_sb.h"

// One schoolbook split, keeping the half a reduction reads. Barrett needs the
// high half of one product and the low half of another, so the rest is skipped.
template<int _BITWIDTH, int _SKIP_UPPER, int _BASE_MUL_WIDTH>
ac_int<2*_BITWIDTH, false> l0_int_mul_par_gen(
    const ac_int<_BITWIDTH, false> x,
    const ac_int<_BITWIDTH, false> y
) {
    static constexpr int l = _BITWIDTH / 2;
    static constexpr int h = _BITWIDTH - l;

    ac_int<l,false> x0 = x.template slc<l>(0);
    ac_int<h,false> x1 = x.template slc<h>(l);
    ac_int<l,false> y0 = y.template slc<l>(0);
    ac_int<h,false> y1 = y.template slc<h>(l);

    ac_int<l+l, false> z0 = 0;
    ac_int<h+h, false> z3 = 0;

    // partial products
    if constexpr (_SKIP_UPPER == 0)
        z0 = l0_int_mul_sb<_BASE_MUL_WIDTH,l,l>(x0, y0);

    auto z1 = l0_int_mul_sb<_BASE_MUL_WIDTH,l,h>(x0, y1);
    auto z2 = l0_int_mul_sb<_BASE_MUL_WIDTH,h,l>(x1, y0);

    if constexpr (_SKIP_UPPER == 1)
        z3 = l0_int_mul_sb<_BASE_MUL_WIDTH,h,h>(x1, y1);

    // recombine
    ac_int<2*_BITWIDTH,false> res = 0;
    res += (ac_int<2*_BITWIDTH,false>) z0;
    res += ((ac_int<2*_BITWIDTH,false>) z1) << l;
    res += ((ac_int<2*_BITWIDTH,false>) z2) << l;
    res += ((ac_int<2*_BITWIDTH,false>) z3) << (l+l);
    return res;
}

template<int _BITWIDTH,
         int _SKIP_UPPER = SKIP_UPPER,
         int _BASE_MUL_WIDTH = BASE_MUL_WIDTH>
class l0_int_mul_par_impl {
    l0_int_mul_impl<_BITWIDTH> int_mul_inst;

public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<2*_BITWIDTH, false> &z
    ) {
        z = l0_int_mul_par_gen<_BITWIDTH,_SKIP_UPPER,_BASE_MUL_WIDTH>(x, y);
    }
};

#endif /* _L0_INT_MUL_PAR_H_ */
