#ifndef _L1_MOD_ADD_MW_H_
#define _L1_MOD_ADD_MW_H_

#include <ac_int.h>
#include "params.h"
#include "l0_int_add.h"
#include "l0_int_sub.h"

// Multi-word modular addition: add, then conditionally subtract q
template<class _FIELD, int _WORD_WIDTH>
ac_int<_FIELD::W, false> l1_mod_add_mw_impl(
    const ac_int<_FIELD::W, false> a,
    const ac_int<_FIELD::W, false> b,
    const ac_int<_FIELD::W, false> q
) {
    static_assert(_FIELD::W % _WORD_WIDTH == 0, "BITWIDTH must be divisible by BASE");

    // TODO: Implement multi-word modular addition
    return 0;
}

#endif /* _L1_MOD_ADD_MW_H_ */
