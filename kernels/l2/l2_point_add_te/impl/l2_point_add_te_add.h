#ifndef _L2_POINT_ADD_TE_ADD_H_
#define _L2_POINT_ADD_TE_ADD_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l1_mod_mul_impl.h"
#include "l1_mod_cmul_impl.h"
#include "l1_mod_add_impl.h"
#include "l1_mod_sub_impl.h"

// Twisted Edwards addition, extended projective
template<class _FIELD, int _MRED>
class l2_point_add_te_add {
    l1_mod_mul_impl<_FIELD, _MRED>          modmul_inst;
    l1_mod_add_impl<_FIELD>                 modadd_inst;
    l1_mod_sub_impl<_FIELD>                 modsub_inst;
    l1_mod_cmul_impl<_FIELD, typename _FIELD::A_MONT, _MRED> cmul_a_mont_inst;
    l1_mod_cmul_impl<_FIELD, typename _FIELD::A, _MRED>      cmul_a_inst;
    l1_mod_cmul_impl<_FIELD, typename _FIELD::D_MONT, _MRED> cmul_d_mont_inst;
    l1_mod_cmul_impl<_FIELD, typename _FIELD::D, _MRED>      cmul_d_inst;

    typedef ac_int<_FIELD::W, false> fe;
    typedef ac_int<l1_mod_mul_consts<_FIELD,_MRED>::RC, false> rc_t;

public:
    void run(
        const PointExtProj<_FIELD> P0,
        const PointExtProj<_FIELD> P1,
        const fe q, const rc_t rc,
        PointExtProj<_FIELD> &R
    ) {
        fe A, B, t0, C, D, t1, t2, t3, t4, E, F, G, t5, H;
        modmul_inst.run(P0.X, P1.X, q, rc, A);       // A = X1*X2
        modmul_inst.run(P0.Y, P1.Y, q, rc, B);       // B = Y1*Y2
        if constexpr (_MRED == MRED_MONT) {          // t0 = d*T2
            cmul_d_mont_inst.run(P1.T, q, rc, t0);
        } else {
            cmul_d_inst.run(P1.T, q, rc, t0);
        }
        modmul_inst.run(P0.T, t0, q, rc, C);         // C = T1*t0
        modmul_inst.run(P0.Z, P1.Z, q, rc, D);       // D = Z1*Z2
        modadd_inst.run(P0.X, P0.Y, q, t1);          // t1 = X1+Y1
        modadd_inst.run(P1.X, P1.Y, q, t2);          // t2 = X2+Y2
        modmul_inst.run(t1, t2, q, rc, t3);          // t3 = t1*t2
        modsub_inst.run(t3, A, q, t4);               // t4 = t3-A
        modsub_inst.run(t4, B, q, E);                // E = t4-B
        modsub_inst.run(D, C, q, F);                 // F = D-C
        modadd_inst.run(D, C, q, G);                 // G = D+C
        if constexpr (_MRED == MRED_MONT) {          // t5 = a*A
            cmul_a_mont_inst.run(A, q, rc, t5);
        } else {
            cmul_a_inst.run(A, q, rc, t5);
        }
        modsub_inst.run(B, t5, q, H);                // H = B-t5

        modmul_inst.run(E, F, q, rc, R.X);           // X3 = E*F
        modmul_inst.run(G, H, q, rc, R.Y);           // Y3 = G*H
        modmul_inst.run(E, H, q, rc, R.T);           // T3 = E*H
        modmul_inst.run(F, G, q, rc, R.Z);           // Z3 = F*G
    }
};

#endif /* _L2_POINT_ADD_TE_ADD_H_ */
