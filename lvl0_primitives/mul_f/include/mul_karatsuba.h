#ifndef _MUL_KARATSUBA_H_
#define _MUL_KARATSUBA_H_

#include "primitives.h"
#include "mul_schoolbook.h"

// Uses Karatsuba to reduce DSP usage
// Cyclone MSM (https://eprint.iacr.org/2022/1396.pdf) Figure 2 - visualizes it well
#if CCORE_MULS == 1
#pragma hls_design ccore
#endif
template<int BW>
ac_int<2*BW, false> mul_karatsuba_gen(
    const ac_int<BW, false> a, 
    const ac_int<BW, false> b
) {
    // Base case
    // +1 ensures karatsuba uneven bitwidths don't result in an extra level
    if constexpr (BW <= (KAR_BASE_MUL_WIDTH+2)) {
        return mul_schoolbook_gen<BW>(a, b);
    } else {        
        static constexpr int H1 = BW / 2;
        static constexpr int H2 = BW - H1; // H2 > H1 if BW is not power of 2
        static constexpr int SW = H2+1;    // sum width

        ac_int<H1, false>   a0 = a.template slc<H1>(0);
        ac_int<H1, false>   b0 = b.template slc<H1>(0);
        ac_int<H2, false>   a1 = a.template slc<BW>(H1);
        ac_int<H2, false>   b1 = b.template slc<BW>(H1);
        
        ac_int<SW, false> sumA = a0 + a1;
        ac_int<SW, false> sumB = b0 + b1;

        ac_int<2*H1, false> z0 = mul_karatsuba_gen<H1>(a0, b0);
        ac_int<2*H2, false> z2 = mul_karatsuba_gen<H2>(a1, b1);
        ac_int<2*SW, false> z1 = mul_karatsuba_gen<SW>(sumA, sumB);

        ac_int<2*SW, false> diff = z1 - z0 - z2; // this will result in a positive
        ac_int<2 * BW, false> diff_ext = (ac_int<2 * BW, false>)diff << H1;
        ac_int<2 * BW, false> z2_ext =   (ac_int<2 * BW, false>)z2 << (2 * H1);
        return z2_ext + diff_ext + z0;
    }
}

#endif // _MUL_KARATSUBA_H_
