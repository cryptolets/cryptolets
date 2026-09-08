#ifndef _L2_POINT_ADD_TE_CYCLONE_H_
#define _L2_POINT_ADD_TE_CYCLONE_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l1_mod_mul_impl.h"
#include "l1_mod_cmul_impl.h"
#include "l1_mod_add_impl.h"
#include "l1_mod_sub_impl.h"

// Twisted Edwards point addition from CycloneMSM paper.
template<class _FIELD, int _MRED=MRED>
class l2_point_add_te_cyclone {
    l1_mod_mul_impl<_FIELD, _MRED>          modmul_inst;
    l1_mod_cmul_impl<_FIELD, _MRED, CMUL_K> modcmul_k_inst;
    l1_mod_add_impl<_FIELD>                 modadd_inst;
    l1_mod_sub_impl<_FIELD>                 modsub_inst;

    typedef ac_int<_FIELD::W, false> fe;
    typedef ac_int<l1_mod_mul_consts<_FIELD,_MRED>::RC, false> rc_t;

public:
    void run(
        const PointExtProj<_FIELD> P0,
        const PointExtProj<_FIELD> P1,
        const fe q, const rc_t rc,
        PointExtProj<_FIELD> &R
    ) {
        fe t0, t1, A, t2, t3, B, t4, C, t5, D, E, F, G, H;
        modsub_inst.run(P0.Y, P0.X, q, t0);          // t0 = Y1-X1
        modsub_inst.run(P1.Y, P1.X, q, t1);          // t1 = Y2-X2
        modmul_inst.run(t0, t1, q, rc, A);           // A = t0*t1
        modadd_inst.run(P0.Y, P0.X, q, t2);          // t2 = Y1+X1
        modadd_inst.run(P1.Y, P1.X, q, t3);          // t3 = Y2+X2
        modmul_inst.run(t2, t3, q, rc, B);           // B = t2*t3
        modcmul_k_inst.run(P1.T, q, rc, t4);         // t4 = k*T2
        modmul_inst.run(P0.T, t4, q, rc, C);         // C = T1*t4
        modadd_inst.run(P1.Z, P1.Z, q, t5);          // t5 = 2*Z2
        modmul_inst.run(P0.Z, t5, q, rc, D);         // D = Z1*t5
        modsub_inst.run(B, A, q, E);                 // E = B-A
        modsub_inst.run(D, C, q, F);                 // F = D-C
        modadd_inst.run(D, C, q, G);                 // G = D+C
        modadd_inst.run(B, A, q, H);                 // H = B+A

        modmul_inst.run(E, F, q, rc, R.X);           // X3 = E*F
        modmul_inst.run(G, H, q, rc, R.Y);           // Y3 = G*H
        modmul_inst.run(E, H, q, rc, R.T);           // T3 = E*H
        modmul_inst.run(F, G, q, rc, R.Z);           // Z3 = F*G
    }
};

#endif /* _L2_POINT_ADD_TE_CYCLONE_H_ */
