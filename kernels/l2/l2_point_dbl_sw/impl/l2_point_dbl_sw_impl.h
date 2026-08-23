#ifndef _L2_POINT_DOUBLE_H_
#define _L2_POINT_DOUBLE_H_

#include <ac_int.h>
#include "params.h"
#include "ec_helper.h"
#include "l2_point_dbl_sw_a0.h"
#include "l2_point_dbl_sw_a3.h"
#include "l2_point_dbl_sw_avar.h"

// The generated top copies the port types, so the width needs its own name
template<class _FIELD, int _MRED>
struct l2_point_dbl_sw_ports {
    static constexpr int RC = l1_mod_mul_ports<_FIELD,_MRED>::RC;
};

template<class _FIELD, int _MRED = MRED, int _PDBL_FORM = PDBL_FORM>
class l2_point_dbl_sw_impl {
    l2_point_dbl_sw_a0<_FIELD, _MRED>   a0_inst;
    l2_point_dbl_sw_a3<_FIELD, _MRED>   a3_inst;
    l2_point_dbl_sw_avar<_FIELD, _MRED> avar_inst;

    typedef ac_int<_FIELD::W, false> fe;
    typedef ac_int<l2_point_dbl_sw_ports<_FIELD,_MRED>::RC, false> rc_t;

public:
    void run(
        const PointJac<_FIELD> P0,
        const ac_int<_FIELD::W, false> q,
        const ac_int<l2_point_dbl_sw_ports<_FIELD,_MRED>::RC, false> rc,
        PointJac<_FIELD> &R
    ) {
        if constexpr (_PDBL_FORM == PDBL_A0) {
            a0_inst.run(P0, q, rc, R);
        } else if constexpr (_PDBL_FORM == PDBL_A3) {
            a3_inst.run(P0, q, rc, R);
        } else { // PDBL_AVAR
            avar_inst.run(P0, q, rc, R);
        }
    }
};

#endif /* _L2_POINT_DOUBLE_H_ */
