#ifndef _L1_MOD_MUL_BARRETT_H_
#define _L1_MOD_MUL_BARRETT_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"
#include "l0_int_mul_par_impl.h"
#include "l0_int_cmul_impl.h"

template<class _FIELD>
class l1_mod_mul_barrett {
    l0_int_mul_impl<_FIELD::W>                        int_mul_inst;
    l0_int_mul_par_impl<2*_FIELD::W, 1>               mul_red_inst;
    l0_int_cmul_impl<_FIELD, CMUL_MU>                 cmul_mu_inst;
    l0_int_cmul_impl<_FIELD, CMUL_Q>                  cmul_q_inst;

public:
    void run(
        const ac_int<_FIELD::W, false> x,
        const ac_int<_FIELD::W, false> y,
        const ac_int<_FIELD::W, false> q,
        const ac_int<2*_FIELD::W, false> mu,
        ac_int<_FIELD::W, false> &z
    ) {
        // t = x * y
        ac_int<2*_FIELD::W, false> t;
        int_mul_inst.run(x, y, t);

        // m = (t * mu) >> 2W, only the high half is read
        ac_int<_FIELD::W, false> m_red;
        if constexpr (REDC_TYPE == FIXED_RC) {
            cmul_mu_inst.run(t, m_red);
        } else {
            ac_int<4*_FIELD::W, false> m;
            mul_red_inst.run(t, mu, m);
            m_red = m.template slc<_FIELD::W>(2*_FIELD::W);
        }

        // m * q
        ac_int<2*_FIELD::W, false> mq;
        if constexpr (Q_TYPE == FIXED_Q) {
            cmul_q_inst.run(m_red, mq);
        } else {
            int_mul_inst.run(m_red, q, mq);
        }

        // t - m*q, which is below 3q
        ac_int<2*_FIELD::W+1, true> t_mq = t - mq;
        ac_int<_FIELD::W+2, false> diff = t_mq.template slc<_FIELD::W+2>(0);

        // z = diff - 2q, diff - q or diff, whichever first lands below q
        ac_int<_FIELD::W+2, true> path1 = diff - 2*q;
        ac_int<_FIELD::W+1, true> path2 = diff - q;
        ac_int<_FIELD::W, false> path3 = (ac_int<_FIELD::W, false>)diff;

        z = (!path1[_FIELD::W+1]) ? (ac_int<_FIELD::W, false>)path1 :
            (!path2[_FIELD::W])   ? (ac_int<_FIELD::W, false>)path2 :
                                    path3;
    }
};

#endif /* _L1_MOD_MUL_BARRETT_H_ */
