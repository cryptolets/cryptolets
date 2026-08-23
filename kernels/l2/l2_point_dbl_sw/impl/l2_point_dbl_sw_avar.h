#ifndef _L2_POINT_DBL_SW_AVAR_H_
#define _L2_POINT_DBL_SW_AVAR_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l1_mod_mul_impl.h"
#include "l1_mod_add_impl.h"
#include "l1_mod_sub_impl.h"
#include "l1_mod_cmul_impl.h"

// Jacobian doubling for any a, dbl-2007-bl
template<class _FIELD, int _MRED>
class l2_point_dbl_sw_avar {
    l1_mod_mul_impl<_FIELD, _MRED> modmul_inst;
    l1_mod_add_impl<_FIELD>        modadd_inst;
    l1_mod_sub_impl<_FIELD>        modsub_inst;
    l1_mod_cmul_impl<_FIELD, _MRED, CMUL_A> cmul_a_inst;

    typedef ac_int<_FIELD::W, false> fe;
    typedef ac_int<l1_mod_mul_ports<_FIELD,_MRED>::RC, false> rc_t;

public:
    void run(
        const PointJac<_FIELD> P0,
        const fe q, const rc_t rc,
        PointJac<_FIELD> &R
    ) {
        fe XX, YY, YYYY, ZZ, t0, t1, t2, t3, S, t4, t5, t6, M, t7, t8, T;
        fe t9, t10, t11, t12, t13, t14;
        modmul_inst.run(P0.X, P0.X, q, rc, XX);      // XX = X1^2
        modmul_inst.run(P0.Y, P0.Y, q, rc, YY);      // YY = Y1^2
        modmul_inst.run(YY, YY, q, rc, YYYY);        // YYYY = YY^2
        modmul_inst.run(P0.Z, P0.Z, q, rc, ZZ);      // ZZ = Z1^2
        modadd_inst.run(P0.X, YY, q, t0);            // t0 = X1+YY
        modmul_inst.run(t0, t0, q, rc, t1);          // t1 = t0^2
        modsub_inst.run(t1, XX, q, t2);              // t2 = t1-XX
        modsub_inst.run(t2, YYYY, q, t3);            // t3 = t2-YYYY
        modadd_inst.run(t3, t3, q, S);               // S = 2*t3
        modmul_inst.run(ZZ, ZZ, q, rc, t4);          // t4 = ZZ^2
        cmul_a_inst.run(t4, q, rc, t5);              // t5 = a*t4
        modadd_inst.run(XX, XX, q, t6);              // t6 = XX+XX
        modadd_inst.run(t6, XX, q, t6);              // t6 = t6+XX
        modadd_inst.run(t6, t5, q, M);               // M = t6+t5
        modmul_inst.run(M, M, q, rc, t7);            // t7 = M^2
        modadd_inst.run(S, S, q, t8);                // t8 = 2*S
        modsub_inst.run(t7, t8, q, T);               // T = t7-t8
        R.X = T;                                     // X3 = T
        modsub_inst.run(S, T, q, t9);                // t9 = S-T
        modadd_inst.run(YYYY, YYYY, q, t10);         // t10 = YYYY+YYYY
        modadd_inst.run(t10, t10, q, t10);           // t10 = t10+t10
        modadd_inst.run(t10, t10, q, t10);           // t10 = t10+t10
        modmul_inst.run(M, t9, q, rc, t11);          // t11 = M*t9
        modsub_inst.run(t11, t10, q, R.Y);           // Y3 = t11-t10
        modadd_inst.run(P0.Y, P0.Z, q, t12);         // t12 = Y1+Z1
        modmul_inst.run(t12, t12, q, rc, t13);       // t13 = t12^2
        modsub_inst.run(t13, YY, q, t14);            // t14 = t13-YY
        modsub_inst.run(t14, ZZ, q, R.Z);            // Z3 = t14-ZZ
    }
};

#endif /* _L2_POINT_DBL_SW_AVAR_H_ */
