#ifndef _EC_HELPER_H_
#define _EC_HELPER_H_

#include <ac_int.h>
#include "params.h"
#include "field_helper.h"

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

// A point in the Montgomery domain carries R on every coordinate
template<class _FIELD>
PointJac<_FIELD> to_mont(const PointJac<_FIELD> P, const ac_int<_FIELD::W, false> q) {
    return {to_mont<_FIELD>(P.X, q), to_mont<_FIELD>(P.Y, q), to_mont<_FIELD>(P.Z, q)};
}

template<class _FIELD>
PointJac<_FIELD> from_mont(const PointJac<_FIELD> P, const ac_int<_FIELD::W, false> q) {
    return {from_mont<_FIELD>(P.X, q), from_mont<_FIELD>(P.Y, q), from_mont<_FIELD>(P.Z, q)};
}

template<class _FIELD>
PointExtProj<_FIELD> to_mont(const PointExtProj<_FIELD> P, const ac_int<_FIELD::W, false> q) {
    return {to_mont<_FIELD>(P.X, q), to_mont<_FIELD>(P.Y, q),
            to_mont<_FIELD>(P.Z, q), to_mont<_FIELD>(P.T, q)};
}

template<class _FIELD>
PointExtProj<_FIELD> from_mont(const PointExtProj<_FIELD> P, const ac_int<_FIELD::W, false> q) {
    return {from_mont<_FIELD>(P.X, q), from_mont<_FIELD>(P.Y, q),
            from_mont<_FIELD>(P.Z, q), from_mont<_FIELD>(P.T, q)};
}

#endif /* _EC_HELPER_H_ */
