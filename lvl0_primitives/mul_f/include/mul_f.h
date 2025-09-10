#ifndef _MUL_F_H_
#define _MUL_F_H_

#include "primitives.h"
#include "mul_schoolbook.h"
#include "mul_karatsuba.h"

template<int BW>
ac_int<2 * BW, false> mul_f_gen(
    const ac_int<BW, false> a,
    const ac_int<BW, false> b
) {
#if MUL_TYPE == MUL_KARATSUBA
    return mul_karatsuba_gen<BW>(a, b);
#elif MUL_TYPE == MUL_SCHOOLBOOK
    return mul_schoolbook_gen<BW>(a, b);
#else // MUL_TYPE == MUL_NORMAL
    return a * b;
#endif
}

wide_2x_t mul_f(
    const wide_t x,
    const wide_t y
);

#endif /* _MUL_F_H_ */
