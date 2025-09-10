#ifndef _SQ_F_H
#define _SQ_F_H

#include "primitives.h"
#include "mul_karatsuba.h"
#include "mul_schoolbook.h"
#include "mul_f.h"

// #pragma hls_design ccore
#if CCORE_MULS == 1
#pragma hls_design ccore
#endif
template<int BW>
ac_int<2*BW, false> sq_f_gen(
    const ac_int<BW, false> a
) {
#if MUL_TYPE == MUL_SCHOOLBOOK
    return mul_schoolbook_gen<BW>(a, a);
#elif MUL_TYPE == MUL_KARATSUBA
    if constexpr (BW <= KAR_BASE_MUL_WIDTH) {
        return mul_schoolbook_gen<BW>(a, a);
    } else {
        static constexpr int H = BW / 2;

        ac_int<H,false> a0 = a.template slc<H>(0);
        ac_int<H,false> a1 = a.template slc<BW>(H);
    
        ac_int<2*H,false> z0 = sq_f_gen<H>(a0);
        ac_int<2*H,false> z1 = mul_karatsuba_gen<H>(a0, a1);
        ac_int<2*H,false> z2 = sq_f_gen<H>(a1);

        // Combine
        ac_int<(3*H)+1, false> z1_ext = (ac_int<(3*H)+1, false>)z1 << (H + 1);
        ac_int<2*BW, false>    z2_ext = (ac_int<2*BW, false>)z2 << (2*H);
        return z2_ext + z1_ext + z0;
    }
#else // MUL_TYPE == MUL_NORMAL
    return a * a;
#endif
}

wide_2x_t sq_f(
    const wide_t a
);

#endif /* _SQ_F_H */
