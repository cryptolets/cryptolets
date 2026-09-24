#ifndef _POINT_ADD_RCB_H_
#define _POINT_ADD_RCB_H_

#include "primitives.h"
#include "modops.h"


EC_point_P point_add_rcb(
    EC_point_P P0, EC_point_A P1 

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

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS)
    , const wide_t field_b3
#endif

);

#endif /* _POINT_ADD_RCB_H_ */
