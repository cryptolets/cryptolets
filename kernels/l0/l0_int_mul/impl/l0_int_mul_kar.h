#ifndef _L0_INT_MUL_KAR_H_
#define _L0_INT_MUL_KAR_H_

#include <ac_int.h>
#include "l0_int_mul_sb.h"

// Recursive Karatsuba multiplication
template<int _BASE_MUL_WIDTH, int _KAR_BASE_MUL_WIDTH, int _BITWIDTH>
ac_int<2*_BITWIDTH, false> l0_int_mul_kar(
    const ac_int<_BITWIDTH, false> x,
    const ac_int<_BITWIDTH, false> y
) {
    // +2 ensures karatsuba uneven bitwidths don't result in an extra level
    if constexpr (_BITWIDTH <= (_KAR_BASE_MUL_WIDTH+2)) {
        return l0_int_mul_sb<_BASE_MUL_WIDTH,_BITWIDTH>(x, y);
    } else {
        static constexpr int H1 = _BITWIDTH / 2;
        static constexpr int H2 = _BITWIDTH - H1; // H2 > H1 if _BITWIDTH is not power of 2
        static constexpr int SW = H2+1;           // sum width

        ac_int<H1, false>   x0 = x.template slc<H1>(0);
        ac_int<H1, false>   y0 = y.template slc<H1>(0);
        ac_int<H2, false>   x1 = x.template slc<_BITWIDTH>(H1);
        ac_int<H2, false>   y1 = y.template slc<_BITWIDTH>(H1);

        ac_int<SW, false> sum_x = x0 + x1;
        ac_int<SW, false> sum_y = y0 + y1;

        ac_int<2*H1, false> z0 = l0_int_mul_kar<_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH,H1>(x0, y0);
        ac_int<2*H2, false> z2 = l0_int_mul_kar<_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH,H2>(x1, y1);
        ac_int<2*SW, false> z1 = l0_int_mul_kar<_BASE_MUL_WIDTH,_KAR_BASE_MUL_WIDTH,SW>(sum_x, sum_y);

        ac_int<2 * SW, false> diff = z1 - z0 - z2; // this will result in a positive
        ac_int<2 * _BITWIDTH, false> diff_ext = (ac_int<2 * _BITWIDTH, false>)diff << H1;
        ac_int<2 * _BITWIDTH, false> z2_ext =   (ac_int<2 * _BITWIDTH, false>)z2 << (2 * H1);
        return z2_ext + diff_ext + z0;
    }
}

#endif /* _L0_INT_MUL_KAR_H_ */
