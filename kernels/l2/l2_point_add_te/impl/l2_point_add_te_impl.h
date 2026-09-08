#ifndef _L2_POINT_ADD_TE_H_
#define _L2_POINT_ADD_TE_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l2_point_add_te_add.h"
#include "l2_point_add_te_cyclone.h"

template<class _FIELD, 
         int _MRED = MRED, 
         int _PADD_TE_FORM = PADD_TE_FORM>
class l2_point_add_te_impl {
    l2_point_add_te_add<_FIELD, _MRED>     add_inst;
    l2_point_add_te_cyclone<_FIELD, _MRED> cyclone_inst;

    typedef ac_int<_FIELD::W, false> fe;

public:
    typedef ac_int<l1_mod_mul_consts<_FIELD,_MRED>::RC, false> rc_t;

    void run(
        const PointExtProj<_FIELD> P0,
        const PointExtProj<_FIELD> P1,
        const ac_int<_FIELD::W, false> q,
        const ac_int<l1_mod_mul_consts<_FIELD,_MRED>::RC, false> rc,
        PointExtProj<_FIELD> &R
    ) {
        if constexpr (_PADD_TE_FORM == PADD_TE_ADD) {
            add_inst.run(P0, P1, q, rc, R);
        } else { // PADD_TE_CYCLONE
            cyclone_inst.run(P0, P1, q, rc, R);
        }
    }
};

#endif /* _L2_POINT_ADD_TE_H_ */
