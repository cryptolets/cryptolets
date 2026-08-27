#ifndef _L1_MOD_CMUL_H_
#define _L1_MOD_CMUL_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_cmul_impl.h"
#include "l1_mont_reduce.h"
#include "l1_barrett_reduce.h"

// One operand is a field constant, so only the multiply differs from a
// l1_mod_mul. The reduction is the same one.
template<class _FIELD, int _MRED = MRED, int _CMUL_CONST = CMUL_CONST>
class l1_mod_cmul_impl {
    // Declared so the shared reductions are on the include path
    l0_int_cmul_impl<_FIELD, _CMUL_CONST> cmul_inst;
    l1_mont_reduce<_FIELD>                mont_inst;
    l1_barrett_reduce<_FIELD>             barrett_inst;

public:
    void run(
        const ac_int<_FIELD::W, false> x,
        const ac_int<_FIELD::W, false> q,
        const ac_int<l1_mod_mul_impl<_FIELD,_MRED>::RC, false> rc,
        ac_int<_FIELD::W, false> &z
    ) {
        // t = x * const
        ac_int<2*_FIELD::W, false> t;
        cmul_inst.run(x, t);

        if constexpr (_MRED == MRED_MONT) {
            mont_inst.run(t, q, rc, z);
        } else {
            barrett_inst.run(t, q, rc, z);
        }
    }
};

#endif /* _L1_MOD_CMUL_H_ */
