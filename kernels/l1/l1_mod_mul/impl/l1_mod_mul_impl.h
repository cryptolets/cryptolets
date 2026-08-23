#ifndef _L1_MOD_MUL_H_
#define _L1_MOD_MUL_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_mul_impl.h"
#include "l1_mont_reduce.h"
#include "l1_barrett_reduce.h"

// The generated top copies the port types, so the width needs its own name
template<class _FIELD, int _MRED>
struct l1_mod_mul_ports {
    // Montgomery reduces by q_prime, Barrett by the wider mu
    static constexpr int RC = (_MRED == MRED_BAR) ? 2*_FIELD::W : _FIELD::W;
};

template<class _FIELD, int _MRED = MRED>
class l1_mod_mul_impl {
    l0_int_mul_impl<_FIELD::W> int_mul_inst;
    l1_mont_reduce<_FIELD>     mont_inst;
    l1_barrett_reduce<_FIELD>  barrett_inst;

public:
    void run(
        const ac_int<_FIELD::W, false> x,
        const ac_int<_FIELD::W, false> y,
        const ac_int<_FIELD::W, false> q,
        const ac_int<l1_mod_mul_ports<_FIELD,_MRED>::RC, false> rc,
        ac_int<_FIELD::W, false> &z
    ) {
        // t = x * y
        ac_int<2*_FIELD::W, false> t;
        int_mul_inst.run(x, y, t);

        if constexpr (_MRED == MRED_MONT) {
            mont_inst.run(t, q, rc, z);
        } else {
            barrett_inst.run(t, q, rc, z);
        }
    }
};

#endif /* _L1_MOD_MUL_H_ */
