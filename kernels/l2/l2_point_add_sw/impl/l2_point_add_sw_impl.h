#ifndef _L2_POINT_ADD_H_
#define _L2_POINT_ADD_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l1_mod_mul_impl.h"
#include "l1_mod_add_impl.h"
#include "l1_mod_sub_impl.h"
#include "l2_point_dbl_sw_impl.h"

// Short Weierstrass point addition 
// with doubling branched after point equality check.

// Should _PDBL_FORM be here?
template<class _FIELD, int _MRED = MRED>
class l2_point_add_sw_impl {
    l1_mod_mul_impl<_FIELD, _MRED>  modmul_inst;
    l1_mod_add_impl<_FIELD>         modadd_inst;
    l1_mod_sub_impl<_FIELD>         modsub_inst;
    l2_point_dbl_sw_impl<_FIELD>    double_inst;

    typedef ac_int<_FIELD::W, false> fe;

public:
    typedef ac_int<l1_mod_mul_consts<_FIELD,_MRED>::RC, false> rc_t;

    void run(
        const PointJac<_FIELD> P0,
        const PointJac<_FIELD> P1,
        const ac_int<_FIELD::W, false> q,
        const ac_int<l1_mod_mul_consts<_FIELD,_MRED>::RC, false> rc,
        PointJac<_FIELD> &R
    ) {
        fe Z1Z1, Z2Z2, U1, U2, t0, S1, t1, S2;
        modmul_inst.run(P0.Z, P0.Z, q, rc, Z1Z1);    // Z1Z1 = Z1^2
        modmul_inst.run(P1.Z, P1.Z, q, rc, Z2Z2);    // Z2Z2 = Z2^2
        modmul_inst.run(P0.X, Z2Z2, q, rc, U1);      // U1 = X1*Z2Z2
        modmul_inst.run(P1.X, Z1Z1, q, rc, U2);      // U2 = X2*Z1Z1
        modmul_inst.run(P1.Z, Z2Z2, q, rc, t0);      // t0 = Z2*Z2Z2
        modmul_inst.run(P0.Y, t0, q, rc, S1);        // S1 = Y1*t0
        modmul_inst.run(P0.Z, Z1Z1, q, rc, t1);      // t1 = Z1*Z1Z1
        modmul_inst.run(P1.Y, t1, q, rc, S2);        // S2 = Y2*t1

        fe H, t2, I, J, t3, r, V;
        modsub_inst.run(U2, U1, q, H);               // H = U2-U1
        modadd_inst.run(H, H, q, t2);                // t2 = 2*H
        modmul_inst.run(t2, t2, q, rc, I);           // I = t2^2
        modmul_inst.run(H, I, q, rc, J);             // J = H*I
        modsub_inst.run(S2, S1, q, t3);              // t3 = S2-S1
        modadd_inst.run(t3, t3, q, r);               // r = 2*t3
        modmul_inst.run(U1, I, q, rc, V);            // V = U1*I

        fe t4, t5, t6, t7, t8, t9, t10;
        PointJac<_FIELD> A;
        modmul_inst.run(r, r, q, rc, t4);            // t4 = r^2
        modadd_inst.run(V, V, q, t5);                // t5 = 2*V
        modsub_inst.run(t4, J, q, t6);               // t6 = t4-J
        modsub_inst.run(t6, t5, q, A.X);             // X3 = t6-t5
        modsub_inst.run(V, A.X, q, t7);              // t7 = V-X3
        modmul_inst.run(S1, J, q, rc, t8);           // t8 = S1*J
        modadd_inst.run(t8, t8, q, t9);              // t9 = 2*t8
        modmul_inst.run(r, t7, q, rc, t10);          // t10 = r*t7
        modsub_inst.run(t10, t9, q, A.Y);            // Y3 = t10-t9

        fe t11, t12, t13, t14;
        modadd_inst.run(P0.Z, P1.Z, q, t11);         // t11 = Z1+Z2
        modmul_inst.run(t11, t11, q, rc, t12);       // t12 = t11^2
        modsub_inst.run(t12, Z1Z1, q, t13);          // t13 = t12-Z1Z1
        modsub_inst.run(t13, Z2Z2, q, t14);          // t14 = t13-Z2Z2
        modmul_inst.run(t14, H, q, rc, A.Z);         // Z3 = t14*H

        // The two points are the same one, so the chord is a tangent
        PointJac<_FIELD> D;
        double_inst.run(P0, q, rc, D);

        bool same = (U1 == U2) && (S1 == S2);
        R.X = same ? D.X : A.X;
        R.Y = same ? D.Y : A.Y;
        R.Z = same ? D.Z : A.Z;
    }
};

#endif /* _L2_POINT_ADD_H_ */
