#ifndef _L2_POINT_DBL_SW_A3_H_
#define _L2_POINT_DBL_SW_A3_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l1_mod_mul_impl.h"
#include "l1_mod_add_impl.h"
#include "l1_mod_sub_impl.h"

// Jacobian doubling for a = -3, dbl-2001-b
template<class _FIELD, int _MRED>
class l2_point_dbl_sw_a3 {
    l1_mod_mul_impl<_FIELD, _MRED> modmul_inst;
    l1_mod_add_impl<_FIELD>        modadd_inst;
    l1_mod_sub_impl<_FIELD>        modsub_inst;

    typedef ac_int<_FIELD::W, false> fe;
    typedef ac_int<l1_mod_mul_consts<_FIELD,_MRED>::RC, false> rc_t;

public:
    // delta = Z1^2, which a caller that already squared Z1 passes in
    void run(
        const PointJac<_FIELD> P0,
        const fe delta,
        const fe q, const rc_t rc,
        PointJac<_FIELD> &R
    ) {
        fe gamma, beta, t0, t1, t2, alpha, t3, t4, t8, t5, t6, t7;
        fe t9, t10, t11, t12;
        modmul_inst.run(P0.Y, P0.Y, q, rc, gamma);   // gamma = Y1^2
        modmul_inst.run(P0.X, gamma, q, rc, beta);   // beta = X1*gamma
        modsub_inst.run(P0.X, delta, q, t0);         // t0 = X1-delta
        modadd_inst.run(P0.X, delta, q, t1);         // t1 = X1+delta
        modmul_inst.run(t0, t1, q, rc, t2);          // t2 = t0*t1
        modadd_inst.run(t2, t2, q, alpha);           // alpha = t2+t2
        modadd_inst.run(t2, alpha, q, alpha);        // alpha = t2+alpha
        modmul_inst.run(alpha, alpha, q, rc, t3);    // t3 = alpha^2
        modadd_inst.run(beta, beta, q, t4);          // t4 = beta+beta
        modadd_inst.run(t4, t4, q, t8);              // t8 = t4+t4
        modadd_inst.run(t8, t8, q, t4);              // t4 = t8+t8
        modsub_inst.run(t3, t4, q, R.X);             // X3 = t3-t4
        modadd_inst.run(P0.Y, P0.Z, q, t5);          // t5 = Y1+Z1
        modmul_inst.run(t5, t5, q, rc, t6);          // t6 = t5^2
        modsub_inst.run(t6, gamma, q, t7);           // t7 = t6-gamma
        modsub_inst.run(t7, delta, q, R.Z);          // Z3 = t7-delta
        modsub_inst.run(t8, R.X, q, t9);             // t9 = t8-X3
        modmul_inst.run(gamma, gamma, q, rc, t10);   // t10 = gamma^2
        modadd_inst.run(t10, t10, q, t11);           // t11 = t10+t10
        modadd_inst.run(t11, t11, q, t11);           // t11 = t11+t11
        modadd_inst.run(t11, t11, q, t11);           // t11 = t11+t11
        modmul_inst.run(alpha, t9, q, rc, t12);      // t12 = alpha*t9
        modsub_inst.run(t12, t11, q, R.Y);           // Y3 = t12-t11
    }
};

#endif /* _L2_POINT_DBL_SW_A3_H_ */
