#ifndef _L1_BARRETT_REDUCE_H_
#define _L1_BARRETT_REDUCE_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"
#include "l0_int_mul_par_impl.h"
#include "l0_int_cmul_impl.h"

// Barrett reduction, t mod q
template<class _FIELD>
class l1_barrett_reduce {
    l0_int_mul_impl<_FIELD::W>          int_mul_inst;
    l0_int_mul_par_impl<2*_FIELD::W, 1> mul_red_inst;
    l0_int_cmul_impl<2*_FIELD::W, typename _FIELD::MU, CMUL_OUTPUT_HI>   cmul_mu_inst;
    l0_int_cmul_impl<_FIELD::W,   typename _FIELD::Q,  CMUL_OUTPUT_FULL> cmul_q_inst;

public:
    void run(
        const ac_int<2*_FIELD::W, false> t,
        const ac_int<_FIELD::W, false> q,
        const ac_int<2*_FIELD::W, false> mu,
        ac_int<_FIELD::W, false> &z
    ) {
        // m = (t * mu) >> 2W, only the high half is read
        ac_int<_FIELD::W, false> m_red;
        if constexpr (REDC_TYPE == FIXED_RC) {
            // The cmul keeps every bit above 2W, but m < q < 2^W
            ac_int<_FIELD::W+1, false> m_hi;
            cmul_mu_inst.run(t, m_hi);
            m_red = m_hi.template slc<_FIELD::W>(0);
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

#endif /* _L1_BARRETT_REDUCE_H_ */
