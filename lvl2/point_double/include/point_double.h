#ifndef _POINT_DOUBLE_H_
#define _POINT_DOUBLE_H_

#include "primitives.h"
#include "modops.h"

EC_point_J point_double_a_0(EC_point_J P0, const ModOps& be);
EC_point_J point_double_a_3(EC_point_J P0, const wide_t Z1Z1, const ModOps& be);
EC_point_J point_double_a_var(EC_point_J P0, const ModOps& be, const wide_t field_a);

EC_point_J point_double(
    EC_point_J P0

#if Q_TYPE == VAR_Q
    , const wide_t q
#endif

#if REDC_TYPE == VAR_RC
    #if MODMUL_TYPE == MODMUL_TYPE_MONT
        , const wide_t q_prime
    #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
        , const wide_2x_t mu
    #endif
#endif

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == AVAR)
    , const wide_t field_a
#endif

);

#endif /* _POINT_DOUBLE_H_ */
