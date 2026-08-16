#ifndef _L1_MOD_ADD_H_
#define _L1_MOD_ADD_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_add_impl.h"
#include "l0_int_sub_impl.h"

template<class _FIELD>
class l1_mod_add_impl {
    l0_int_add_impl<_FIELD::W>   int_add_inst;
    l0_int_sub_impl<_FIELD::W+1> int_sub_inst;

public:
    void run(
        const ac_int<_FIELD::W, false> a,
        const ac_int<_FIELD::W, false> b,
        const ac_int<_FIELD::W, false> q,
        ac_int<_FIELD::W, false> &z
    ) {
        ac_int<_FIELD::W+1, false> adder_out;
        ac_int<_FIELD::W+2, true> reduced_out;

        int_add_inst.run(a, b, adder_out);
        int_sub_inst.run(adder_out, q, reduced_out);

        // Use reduced_out only if non-negative
        z = (!reduced_out[_FIELD::W+1]) ? (ac_int<_FIELD::W, false>)reduced_out :
                                          (ac_int<_FIELD::W, false>)adder_out;
    }
};

#endif /* _L1_MOD_ADD_H_ */
