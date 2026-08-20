#ifndef _L1_MOD_MUL_MONT_H_
#define _L1_MOD_MUL_MONT_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"
#include "l0_int_cmul_impl.h"
#include "l0_int_sub_impl.h"

template<class _FIELD>
class l1_mod_mul_mont_impl {
    l0_int_mul_impl<_FIELD::W>             int_mul_inst;
    l0_int_cmul_impl<_FIELD, CMUL_Q_PRIME> cmul_q_prime_inst;
    l0_int_cmul_impl<_FIELD, CMUL_Q>       cmul_q_inst;
    l0_int_sub_impl<_FIELD::W+1>           int_sub_inst;

public:
    void run(
        const ac_int<_FIELD::W, false> x,
        const ac_int<_FIELD::W, false> y,
        const ac_int<_FIELD::W, false> q,
        const ac_int<_FIELD::W, false> q_prime,
        ac_int<_FIELD::W, false> &z
    ) {
        // t = x * y
        ac_int<2*_FIELD::W, false> t;
        int_mul_inst.run(x, y, t);

        ac_int<_FIELD::W, false> t_red = t.template slc<_FIELD::W>(0); // t & (R-1)

        // (t_red * q_prime) & (R-1)
        ac_int<_FIELD::W, false> m_red;
        if constexpr (REDC_TYPE == FIXED_RC) {
            cmul_q_prime_inst.run(t_red, m_red); // compile to constant multiplier
        } else {
            ac_int<2*_FIELD::W, false> m;
            int_mul_inst.run(t_red, q_prime, m);
            m_red = m.template slc<_FIELD::W>(0); // Extract lower BITWIDTH bits
        }

        // m * q
        ac_int<2*_FIELD::W, false> mq;
        if constexpr (Q_TYPE == FIXED_Q) {
            cmul_q_inst.run(m_red, mq); // compile to constant multiplier
        } else {
            int_mul_inst.run(m_red, q, mq);
        }

        // u = (t + m*q) / R
        ac_int<2*_FIELD::W+1, false> t_mq = t + mq;
        ac_int<_FIELD::W+1, false> u = t_mq >> _FIELD::W;

        // u - q
        ac_int<_FIELD::W+2, true> diff;
        int_sub_inst.run(u, q, diff);

        // z = u >= q ? u - q : u
        z = (!diff[_FIELD::W+1]) ? (ac_int<_FIELD::W, false>)diff :
                                   (ac_int<_FIELD::W, false>)u;
    }
};

#endif /* _L1_MOD_MUL_MONT_H_ */
