#ifndef _L0_INT_MUL_SB_H_
#define _L0_INT_MUL_SB_H_

#include <ac_int.h>

// Recursive schoolbook multiplication
template<int _BASE_MUL_WIDTH, int _BW_X, int _BW_Y=_BW_X>
ac_int<_BW_X+_BW_Y,false> l0_int_mul_sb(
    const ac_int<_BW_X,false> x,
    const ac_int<_BW_Y,false> y
) {
    // +2 ensures karatsuba uneven bitwidths don't result in an extra level
    if constexpr ((_BW_X <= (_BASE_MUL_WIDTH+2)) && (_BW_Y <= (_BASE_MUL_WIDTH+2))) {
        return x * y;
    } else {
        // split x
        static constexpr int lx = _BW_X / 2;
        static constexpr int hx = _BW_X - lx;

        // split y
        static constexpr int ly = _BW_Y / 2;
        static constexpr int hy = _BW_Y - ly;

        ac_int<lx,false> x0 = x.template slc<lx>(0);
        ac_int<hx,false> x1 = x.template slc<hx>(lx);
        ac_int<ly,false> y0 = y.template slc<ly>(0);
        ac_int<hy,false> y1 = y.template slc<hy>(ly);

        // recursive partial products
        auto z0 = l0_int_mul_sb<_BASE_MUL_WIDTH,lx,ly>(x0, y0);
        auto z1 = l0_int_mul_sb<_BASE_MUL_WIDTH,lx,hy>(x0, y1);
        auto z2 = l0_int_mul_sb<_BASE_MUL_WIDTH,hx,ly>(x1, y0);
        auto z3 = l0_int_mul_sb<_BASE_MUL_WIDTH,hx,hy>(x1, y1);

        // recombine
        ac_int<_BW_X+_BW_Y,false> res = 0;
        res += (ac_int<_BW_X+_BW_Y,false>) z0;
        res += ((ac_int<_BW_X+_BW_Y,false>) z1) << ly;
        res += ((ac_int<_BW_X+_BW_Y,false>) z2) << lx;
        res += ((ac_int<_BW_X+_BW_Y,false>) z3) << (lx+ly);

        return res;
    }
}

#endif /* _L0_INT_MUL_SB_H_ */
