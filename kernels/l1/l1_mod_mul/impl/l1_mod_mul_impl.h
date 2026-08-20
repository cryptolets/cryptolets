#ifndef _L1_MOD_MUL_H_
#define _L1_MOD_MUL_H_

#include <ac_int.h>
#include "params.h"
#include "l1_mod_mul_mont.h"
#include "l1_mod_mul_barrett.h"

// The generated top copies the port types, so the width needs its own name
template<class _FIELD, int _MRED>
struct l1_mod_mul_ports {
    // Montgomery reduces by q_prime, Barrett by the wider mu
    static constexpr int RC = (_MRED == MRED_BAR) ? 2*_FIELD::W : _FIELD::W;
};

template<class _FIELD, int _MRED = MRED>
class l1_mod_mul_impl {
    l1_mod_mul_mont<_FIELD>    mont_inst;
    l1_mod_mul_barrett<_FIELD> barrett_inst;

public:
    void run(
        const ac_int<_FIELD::W, false> x,
        const ac_int<_FIELD::W, false> y,
        const ac_int<_FIELD::W, false> q,
        const ac_int<l1_mod_mul_ports<_FIELD,_MRED>::RC, false> rc,
        ac_int<_FIELD::W, false> &z
    ) {
        if constexpr (_MRED == MRED_MONT) {
            mont_inst.run(x, y, q, rc, z);
        } else {
            barrett_inst.run(x, y, q, rc, z);
        }
    }
};

#endif /* _L1_MOD_MUL_H_ */
