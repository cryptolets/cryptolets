#ifndef _FIELD_HELPER_H_
#define _FIELD_HELPER_H_

#include <ac_int.h>
#include "params.h"

// Plain modular arithmetic and the Montgomery domain, 
// which only the testbench runs.

// x * y mod q
template<class _FIELD>
ac_int<_FIELD::W, false> mod_mul(const ac_int<_FIELD::W, false> x,
                                 const ac_int<_FIELD::W, false> y,
                                 const ac_int<_FIELD::W, false> q) {
    ac_int<2*_FIELD::W, false> t = x * y;
    return (ac_int<_FIELD::W, false>)(t % q);
}

// x^-1 mod q by the extended euclidean algorithm
template<class _FIELD>
ac_int<_FIELD::W, false> mod_inv(const ac_int<_FIELD::W, false> x,
                                 const ac_int<_FIELD::W, false> q) {
    ac_int<2*_FIELD::W, true> r = q, new_r = x;
    ac_int<2*_FIELD::W, true> t = 0, new_t = 1;

    while (new_r != 0) {
        ac_int<2*_FIELD::W, true> quot = r / new_r;
        ac_int<2*_FIELD::W, true> tmp = t - quot * new_t;
        t = new_t; new_t = tmp;
        tmp = r - quot * new_r;
        r = new_r; new_r = tmp;
    }
    if (t < 0) t += q;
    return (ac_int<_FIELD::W, false>)t;
}

// Montgomery domain helper functions
template<class _FIELD>
ac_int<_FIELD::W, false> mont_r(const ac_int<_FIELD::W, false> q) {
    ac_int<_FIELD::W+1, false> r = 1;
    return (ac_int<_FIELD::W, false>)((r << _FIELD::W) % q);
}

template<class _FIELD>
ac_int<_FIELD::W, false> to_mont(const ac_int<_FIELD::W, false> x,
                                 const ac_int<_FIELD::W, false> q) {
    return mod_mul<_FIELD>(x, mont_r<_FIELD>(q), q);
}

template<class _FIELD>
ac_int<_FIELD::W, false> from_mont(const ac_int<_FIELD::W, false> x,
                                   const ac_int<_FIELD::W, false> q) {
    return mod_mul<_FIELD>(x, mod_inv<_FIELD>(mont_r<_FIELD>(q), q), q);
}

#endif /* _FIELD_HELPER_H_ */
