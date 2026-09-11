#ifndef _L1_MUL_PAR_H_
#define _L1_MUL_PAR_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"

// One schoolbook split keeping only the high half, which is all Barrett reads.
// The low quadrant is never computed, so its carry into the high half is lost,
// leaving m an underestimate the reduction's correction steps already absorb.
// Both operands of every quadrant are padded to h, since the multiplier takes
// one width, and a zero-extended operand multiplies the same.
template<int _BITWIDTH>
class l1_mul_par {
    l0_int_mul_impl<_BITWIDTH - _BITWIDTH/2> mul_inst;

public:
    void run(
        const ac_int<_BITWIDTH, false> x,
        const ac_int<_BITWIDTH, false> y,
        ac_int<2*_BITWIDTH, false> &z
    ) {
        static constexpr int l = _BITWIDTH / 2;
        static constexpr int h = _BITWIDTH - l;

        ac_int<h,false> x0 = x.template slc<l>(0);
        ac_int<h,false> x1 = x.template slc<h>(l);
        ac_int<h,false> y0 = y.template slc<l>(0);
        ac_int<h,false> y1 = y.template slc<h>(l);

        ac_int<2*h, false> z1, z2, z3;
        mul_inst.run(x0, y1, z1);
        mul_inst.run(x1, y0, z2);
        mul_inst.run(x1, y1, z3);

        ac_int<2*_BITWIDTH,false> res = 0;
        res += ((ac_int<2*_BITWIDTH,false>) z1) << l;
        res += ((ac_int<2*_BITWIDTH,false>) z2) << l;
        res += ((ac_int<2*_BITWIDTH,false>) z3) << (l+l);
        z = res;
    }
};

#endif /* _L1_MUL_PAR_H_ */
