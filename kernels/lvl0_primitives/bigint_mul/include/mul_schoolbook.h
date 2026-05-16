#ifndef _MUL_SCHOOLBOOK_H_
#define _MUL_SCHOOLBOOK_H_

#include <ac_int.h>
#include "params.h"

// Recursive schoolbook multiplier for arbitrary BW
// Works for odd and even bitwidths
template<int _N_A, int _N_B=_N_A>
ac_int<_N_A+_N_B,false> mul_schoolbook(
    const ac_int<_N_A,false> a,
    const ac_int<_N_B,false> b
) {
    // +1 ensures karatsuba uneven bitwidths don't result in an extra level
    if constexpr ((_N_A <= (BASE_MUL_WIDTH+2)) && (_N_B <= (BASE_MUL_WIDTH+2))) {
        return a * b;
    } else {
        // split a
        static constexpr int la = _N_A / 2;
        static constexpr int ha = _N_A - la;
        
        // split b
        static constexpr int lb = _N_B / 2;
        static constexpr int hb = _N_B - lb;

        ac_int<la,false> a0 = a.template slc<la>(0);
        ac_int<ha,false> a1 = a.template slc<ha>(la);
        ac_int<lb,false> b0 = b.template slc<lb>(0);
        ac_int<hb,false> b1 = b.template slc<hb>(lb);

        // recursive partial products
        auto z0 = mul_schoolbook<la,lb>(a0, b0);
        auto z1 = mul_schoolbook<la,hb>(a0, b1);
        auto z2 = mul_schoolbook<ha,lb>(a1, b0);
        auto z3 = mul_schoolbook<ha,hb>(a1, b1);

        // recombine
        ac_int<_N_A+_N_B,false> res = 0;
        res += (ac_int<_N_A+_N_B,false>) z0;
        res += ((ac_int<_N_A+_N_B,false>) z1) << lb;
        res += ((ac_int<_N_A+_N_B,false>) z2) << la;
        res += ((ac_int<_N_A+_N_B,false>) z3) << (la+lb);

        return res;
    }
}

#endif // _MUL_SCHOOLBOOK_H_
