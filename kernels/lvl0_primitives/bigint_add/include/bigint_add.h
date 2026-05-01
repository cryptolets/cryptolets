#ifndef _ADD_F_H_
#define _ADD_F_H_

#include "primitives.h"

ac_int<N+1, false> bigint_add_inst(
    const ac_int<N, false> x, 
    const ac_int<N, false> y
);

template<int N, bool MULTI_WORD = false, int BASE = 32>
ac_int<N+1, false> bigint_add(
    const ac_int<N, false> x,
    const ac_int<N, false> y
) {
    if constexpr (!MULTI_WORD) {
        return x + y;
    } else {
        // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
        // 14.7 Algorithm Multiple-precision addition
        // Note: DIGITS = n+1, BASE = b (variable name mapping to reference)
        static_assert(N % BASE == 0, "N must be divisible by BASE");
        static constexpr int DIGITS = N / BASE;

        ac_int<N+1, false> w;
        ac_int<1, false> c = 0; // c <- 0

        // 2.
        for (int i = 0; i < DIGITS; i++) {
            // 2.1 w_i <- (x_i + y_i + c) mod b
            ac_int<BASE+1, false> w_i_ext = x.slc<BASE>(i * BASE) + y.slc<BASE>(i * BASE) + c;
            w.set_slc(i*BASE, w_i_ext.slc<BASE>(0));

            // Note: same logic more hardware friendly
            // 2.2 If (x_i + y_i + c) < b then c <- 0; otherwise c <- 1
            c = w_i_ext[BASE];
        }

        w[N] = c; // 3. w_(n+1) <- c
        return w; // 4.
    }
}

#endif /* _ADD_F_H_ */
