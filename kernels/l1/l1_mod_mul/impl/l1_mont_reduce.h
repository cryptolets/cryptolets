#ifndef _L1_MONT_REDUCE_H_
#define _L1_MONT_REDUCE_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"
#include "l0_int_cmul_impl.h"

// Montgomery reduction, t * R^-1 mod q
template<class _FIELD>
class l1_mont_reduce {
    l0_int_mul_impl<_FIELD::W>                 int_mul_inst;
    l0_int_mul_impl<_FIELD::W, MUL_OUTPUT_LO>  mul_lo_inst;
    l0_int_cmul_impl<_FIELD::W, typename _FIELD::Q_PRIME, CMUL_OUTPUT_LO>   cmul_q_prime_inst;
    l0_int_cmul_impl<_FIELD::W, typename _FIELD::Q,       CMUL_OUTPUT_FULL> cmul_q_inst;

public:
    void run(
        const ac_int<2*_FIELD::W, false> t,
        const ac_int<_FIELD::W, false> q,
        const ac_int<_FIELD::W, false> q_prime,
        ac_int<_FIELD::W, false> &z
    ) {
        ac_int<_FIELD::W, false> t_red = t.template slc<_FIELD::W>(0); // t & (R-1)

        // (t_red * q_prime) & (R-1)
        ac_int<_FIELD::W, false> m_red;
        if constexpr (REDC_TYPE == FIXED_RC) {
            cmul_q_prime_inst.run(t_red, m_red); // compile to constant multiplier
        } else {
            ac_int<2*_FIELD::W, false> m;
            mul_lo_inst.run(t_red, q_prime, m); // only the low half is read
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
        ac_int<_FIELD::W+2, true> diff = u - q;

        // z = u >= q ? u - q : u
        z = (!diff[_FIELD::W+1]) ? (ac_int<_FIELD::W, false>)diff :
                                   (ac_int<_FIELD::W, false>)u;
    }
};

#endif /* _L1_MONT_REDUCE_H_ */
