#ifndef _EC_HELPER_H_
#define _EC_HELPER_H_

#include <ac_int.h>
#include "params.h"

// A point in each coordinate system the formulas work in, and the
// conversions between them, which only the testbench runs.

// Affine
template<class _FIELD>
struct PointAff {
    ac_int<_FIELD::W, false> x, y;
};

// Jacobian
template<class _FIELD>
struct PointJac {
    ac_int<_FIELD::W, false> X, Y, Z;
};

// Extended projective
template<class _FIELD>
struct PointExtProj {
    ac_int<_FIELD::W, false> X, Y, Z, T;
};

// The conversions need plain modular arithmetic, which no kernel runs
// x * y mod q, on a width that holds the product
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


// Z is free, so a converted affine point takes the cheapest one

// affine to jacobian
template<class _FIELD>
PointJac<_FIELD> aff_to_jac(const PointAff<_FIELD> P) {
    PointJac<_FIELD> R;
    R.X = P.x;
    R.Y = P.y;
    R.Z = 1;
    return R;
}

// affine to extended projective
template<class _FIELD>
PointExtProj<_FIELD> aff_to_ext_proj(const PointAff<_FIELD> P,
                                     const ac_int<_FIELD::W, false> q) {
    PointExtProj<_FIELD> R;
    R.X = P.x;
    R.Y = P.y;
    R.Z = 1;
    R.T = mod_mul<_FIELD>(P.x, P.y, q);
    return R;
}

// Converting back needs a modular inverse, which the testbench alone runs

// jacobian to affine
// x = X/Z^2 and y = Y/Z^3
template<class _FIELD>
PointAff<_FIELD> jac_to_aff(const PointJac<_FIELD> P,
                            const ac_int<_FIELD::W, false> q) {
    PointAff<_FIELD> R;
    if (P.Z == 0) { R.x = 0; R.y = 0; return R; }

    ac_int<_FIELD::W, false> z2 = mod_mul<_FIELD>(P.Z, P.Z, q);
    ac_int<_FIELD::W, false> z3 = mod_mul<_FIELD>(z2, P.Z, q);
    R.x = mod_mul<_FIELD>(P.X, mod_inv<_FIELD>(z2, q), q);
    R.y = mod_mul<_FIELD>(P.Y, mod_inv<_FIELD>(z3, q), q);
    return R;
}

// extended projective to affine
// x = X/Z and y = Y/Z
template<class _FIELD>
PointAff<_FIELD> ext_proj_to_aff(const PointExtProj<_FIELD> P,
                                 const ac_int<_FIELD::W, false> q) {
    PointAff<_FIELD> R;
    if (P.Z == 0) { R.x = 0; R.y = 0; return R; }

    ac_int<_FIELD::W, false> z_inv = mod_inv<_FIELD>(P.Z, q);
    R.x = mod_mul<_FIELD>(P.X, z_inv, q);
    R.y = mod_mul<_FIELD>(P.Y, z_inv, q);
    return R;
}

#endif /* _EC_HELPER_H_ */
