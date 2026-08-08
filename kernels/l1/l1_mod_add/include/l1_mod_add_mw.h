#ifndef _L1_MOD_ADD_MW_H_
#define _L1_MOD_ADD_MW_H_

#include <ac_int.h>
#include "params.h"
#include "l0_add.h"
#include "l0_sub.h"

// Multi-word modular addition: add, then conditionally subtract q
template<int _N, int _BASE>
ac_int<_N, false> l1_mod_add_mw(
    const ac_int<_N, false> a,
    const ac_int<_N, false> b,
    const ac_int<_N, false> q
) {
    static_assert(_N % _BASE == 0, "N must be divisible by BASE");

    // TODO: Implement multi-word modular addition
    return 0;
}

#endif /* _L1_MOD_ADD_MW_H_ */
