#ifndef BIGINT_MUL_H
#define BIGINT_MUL_H

#include <ac_int.h>
#include "params.h"
#include "mul_schoolbook.h"
#include "mul_karatsuba.h"

// Forward declarations
template<int _N, int _BASE>
ac_int<2*_N, false> mul_mw(const ac_int<_N, false> a, const ac_int<_N, false> b);

template<int _N_A, int _N_B>
ac_int<_N_A + _N_B, false> bigint_mul_core(const ac_int<_N_A, false> a, const ac_int<_N_B, false> b);

// Interface function
template <int _N, bool _MULTI_WORD = false, int _BASE = 32>
ac_int<2*_N, false> bigint_mul(
    const ac_int<_N, false> a,
    const ac_int<_N, false> b
) {
    if constexpr (!_MULTI_WORD) {
        return bigint_mul_core<_N, _N>(a, b);
    } else {
        return mul_mw<_N, _BASE>(a, b);
    }
}

// Single-word multiplication
template<int _N_A, int _N_B>
ac_int<_N_A + _N_B, false> bigint_mul_core(
    const ac_int<_N_A, false> a,
    const ac_int<_N_B, false> b
) {
#if MUL_TYPE == MUL_KARATSUBA
    static_assert(_N_A == _N_B, "Karatsuba multiplier requires _N_A == _N_B");
    return mul_karatsuba<_N_A>(a, b);
#elif MUL_TYPE == MUL_SCHOOLBOOK
    return mul_schoolbook<_N_A, _N_B>(a, b);
#else // MUL_TYPE == MUL_BASELINE
    return a * b; // This uses Catapult's native multiplier
#endif
}

// Multiple-word multiplication
template<int _N, int _BASE>
ac_int<2*_N, false> mul_mw(
    const ac_int<_N, false> a,
    const ac_int<_N, false> b
) {
    // https://cacr.uwaterloo.ca/hac/about/chap14.pdf
    // 14.12 Algorithm Multiple-precision multiplication
    // Note: DIGITS = n+1, BASE = b (variable name mapping to reference)
    static_assert(_N % _BASE == 0, "N must be divisible by BASE");
    static constexpr int DIGITS = _N / _BASE;
    
    ac_int<2*_N, false> w = 0; // 1. zero out

    // 2.
    for (int i=0; i<DIGITS; i++) {
        ac_int<_BASE, false> c = 0; // c <- 0
        for (int j=0; j<DIGITS; j++) {
            ac_int<2*_N, false> prod = bigint_mul<_BASE>(a.slc<_BASE>(j*_BASE), b.slc<_BASE>(i*_BASE)); // x_j * y_j
            ac_int<2*_N, false> w_i_j = w.slc<_BASE>((i+j)*_BASE); // get w_(i+j)
            ac_int<2*_N, false> uv = w_i_j + prod + c; // (uv)_b = w_(i+j) + (x_j) * (y_i) + c
            w.set_slc((i+j)*_BASE, uv.slc<_BASE>(0)); // set w_(i+j) <- v
            c = uv.slc<_BASE>(_BASE); // set c <- u
        }
        w.set_slc((i+DIGITS)*_BASE, c); // w_(i+n+1)
    }
    
    return w; // 3.
}

#endif // BIGINT_MUL_H
