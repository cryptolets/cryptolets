#ifndef _POINT_ADD_TE_H_
#define _POINT_ADD_TE_H_

#include "primitives.h"
#include "modops.h"


EC_point_EP point_add_te(
    EC_point_EP P0, EC_point_EP P1 

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
    , const wide_t field_a, const wide_t field_d
#endif

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == ANEG1)
    , const wide_t field_k
#endif

);

#endif /* _POINT_ADD_TE_H_ */
