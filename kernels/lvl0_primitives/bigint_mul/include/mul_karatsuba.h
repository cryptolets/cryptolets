#ifndef _MUL_KARATSUBA_H_
#define _MUL_KARATSUBA_H_

#include <ac_int.h>
#include "params.h"
#include "mul_schoolbook.h"

// Karatsuba algorithm reference:
// Anatolii Alexeevich Karatsuba. 1995. The complexity of computations. 
// Proceedings of the Steklov Institute of Mathematics-Interperiodica Translation 211 (1995), 169–183.

// Use Karatsuba to reduce area in asic and dsp usage in fpgas
template<int _N>
ac_int<2*_N, false> mul_karatsuba(
    const ac_int<_N, false> a, 
    const ac_int<_N, false> b
) {
    // Base case
    // +1 ensures karatsuba uneven bitwidths don't result in an extra level
    if constexpr (_N <= (KAR_BASE_MUL_WIDTH+2)) {
        return mul_schoolbook<_N>(a, b);
    } else {     
        static constexpr int H1 = _N / 2;
        static constexpr int H2 = _N - H1; // H2 > H1 if _N is not power of 2
        static constexpr int SW = H2+1;    // sum width

        ac_int<H1, false>   a0 = a.template slc<H1>(0);
        ac_int<H1, false>   b0 = b.template slc<H1>(0);
        ac_int<H2, false>   a1 = a.template slc<_N>(H1);
        ac_int<H2, false>   b1 = b.template slc<_N>(H1);
        
        ac_int<SW, false> sumA = a0 + a1;
        ac_int<SW, false> sumB = b0 + b1;

        ac_int<2*H1, false> z0 = mul_karatsuba<H1>(a0, b0);
        ac_int<2*H2, false> z2 = mul_karatsuba<H2>(a1, b1);
        ac_int<2*SW, false> z1 = mul_karatsuba<SW>(sumA, sumB);

        ac_int<2 * SW, false> diff = z1 - z0 - z2; // this will result in a positive
        ac_int<2 * _N, false> diff_ext = (ac_int<2 * _N, false>)diff << H1;
        ac_int<2 * _N, false> z2_ext =   (ac_int<2 * _N, false>)z2 << (2 * H1);
        return z2_ext + diff_ext + z0;
    }
}

#endif // _MUL_KARATSUBA_H_
