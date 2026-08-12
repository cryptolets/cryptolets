#ifndef _L1_MOD_ADD_H_
#define _L1_MOD_ADD_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_add.h"
#include "l0_int_sub.h"

template<class _FIELD>
ac_int<_FIELD::W, false> l1_mod_add_impl(
    const ac_int<_FIELD::W, false> a,
    const ac_int<_FIELD::W, false> b,
    const ac_int<_FIELD::W, false> q
) {
    ac_int<_FIELD::W+1, false> adder_out = l0_int_add_impl<_FIELD::W>(a, b);
    ac_int<_FIELD::W+1, true> reduced_out = l0_int_sub_impl<_FIELD::W+1>(adder_out, q);

    // Use reduced_out only if non-negative
    return (!reduced_out[_FIELD::W]) ? (ac_int<_FIELD::W, false>)reduced_out :
                                  (ac_int<_FIELD::W, false>)adder_out;
}

#endif /* _L1_MOD_ADD_H_ */
