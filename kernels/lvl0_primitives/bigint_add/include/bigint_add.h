#ifndef _BIGINT_ADD_H_
#define _BIGINT_ADD_H_

#include <ac_int.h>
#include "params.h"

template<int _N, bool _MULTI_WORD = false, int _BASE = 32>
ac_int<_N+1, false> bigint_add(
    const ac_int<_N, false> x,
    const ac_int<_N, false> y
) {
    if constexpr (!_MULTI_WORD) {
        return x + y;
    } else {
        // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
        // 14.7 Algorithm Multiple-precision addition
        // Note: DIGITS = n+1, BASE = b (variable name mapping to reference)
        static_assert(_N % _BASE == 0, "N must be divisible by BASE");
        static constexpr int DIGITS = _N / _BASE;

        ac_int<_N+1, false> w;
        ac_int<1, false> c = 0; // c <- 0

        // 2.
        for (int i = 0; i < DIGITS; i++) {
            // 2.1 w_i <- (x_i + y_i + c) mod b
            ac_int<_BASE+1, false> w_i_ext = x.slc<_BASE>(i * _BASE) + y.slc<_BASE>(i * _BASE) + c;
            w.set_slc(i*_BASE, w_i_ext.slc<_BASE>(0));

            // Note: same logic more hardware friendly
            // 2.2 If (x_i + y_i + c) < b then c <- 0; otherwise c <- 1
            c = w_i_ext[_BASE];
        }

        w[_N] = c; // 3. w_(n+1) <- c
        return w; // 4.
    }
}

#endif /* _BIGINT_ADD_H_ */
