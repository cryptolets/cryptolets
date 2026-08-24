#ifndef _L2_POINT_DBL_SW_A0_H_
#define _L2_POINT_DBL_SW_A0_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l1_mod_mul_impl.h"
#include "l1_mod_add_impl.h"
#include "l1_mod_sub_impl.h"

// Jacobian doubling for a = 0, dbl-2009-l
template<class _FIELD, int _MRED>
class l2_point_dbl_sw_a0 {
    l1_mod_mul_impl<_FIELD, _MRED> modmul_inst;
    l1_mod_add_impl<_FIELD>        modadd_inst;
    l1_mod_sub_impl<_FIELD>        modsub_inst;

    typedef ac_int<_FIELD::W, false> fe;
    typedef ac_int<l1_mod_mul_impl<_FIELD,_MRED>::RC, false> rc_t;

public:
    void run(
        const PointJac<_FIELD> P0,
        const fe q, const rc_t rc,
        PointJac<_FIELD> &R
    ) {
        fe A, B, C, t0, t1, t2, t3, D, E, F, t4, t5, t6, t7, t8;
        modmul_inst.run(P0.X, P0.X, q, rc, A);      // A = X1^2
        modmul_inst.run(P0.Y, P0.Y, q, rc, B);      // B = Y1^2
        modmul_inst.run(B, B, q, rc, C);            // C = B^2
        modadd_inst.run(P0.X, B, q, t0);            // t0 = X1+B
        modmul_inst.run(t0, t0, q, rc, t1);         // t1 = t0^2
        modsub_inst.run(t1, A, q, t2);              // t2 = t1-A
        modsub_inst.run(t2, C, q, t3);              // t3 = t2-C
        modadd_inst.run(t3, t3, q, D);              // D = 2*t3
        modadd_inst.run(A, A, q, E);                // E = A+A
        modadd_inst.run(E, A, q, E);                // E = E+A
        modmul_inst.run(E, E, q, rc, F);            // F = E^2
        modadd_inst.run(D, D, q, t4);               // t4 = 2*D
        modsub_inst.run(F, t4, q, R.X);             // X3 = F-t4
        modsub_inst.run(D, R.X, q, t5);             // t5 = D-X3
        modadd_inst.run(C, C, q, t6);               // t6 = C+C
        modadd_inst.run(t6, t6, q, t6);             // t6 = t6+t6
        modadd_inst.run(t6, t6, q, t6);             // t6 = t6+t6
        modmul_inst.run(E, t5, q, rc, t7);          // t7 = E*t5
        modsub_inst.run(t7, t6, q, R.Y);            // Y3 = t7-t6
        modmul_inst.run(P0.Y, P0.Z, q, rc, t8);     // t8 = Y1*Z1
        modadd_inst.run(t8, t8, q, R.Z);            // Z3 = 2*t8
    }
};

#endif /* _L2_POINT_DBL_SW_A0_H_ */
