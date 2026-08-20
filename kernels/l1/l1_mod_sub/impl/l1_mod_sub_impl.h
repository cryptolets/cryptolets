#ifndef _L1_MOD_SUB_H_
#define _L1_MOD_SUB_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_add_impl.h"
#include "l0_int_sub_impl.h"

template<class _FIELD>
class l1_mod_sub_impl {
    l0_int_sub_impl<_FIELD::W>   int_sub_inst;
    l0_int_add_impl<_FIELD::W+1> int_add_inst;

public:
    void run(
        const ac_int<_FIELD::W, false> a,
        const ac_int<_FIELD::W, false> b,
        const ac_int<_FIELD::W, false> q,
        ac_int<_FIELD::W, false> &z
    ) {
        ac_int<_FIELD::W+1, true>  diff;
        ac_int<_FIELD::W+2, false> adder_out;

        int_sub_inst.run(a, b, diff);
        int_add_inst.run(diff, q, adder_out);

        // Add q back only when the difference went negative
        z = (!diff[_FIELD::W]) ? (ac_int<_FIELD::W, false>)diff :
                                 (ac_int<_FIELD::W, false>)adder_out;
    }
};

#endif /* _L1_MOD_SUB_H_ */
