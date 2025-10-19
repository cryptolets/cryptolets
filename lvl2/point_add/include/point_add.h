#ifndef _POINT_ADD_H_
#define _POINT_ADD_H_

#include "primitives.h"
#include "modops.h"

EC_point_J point_add(
    EC_point_J P0, EC_point_J P1

#if Q_TYPE == VAR_Q
    , const wide_t q
#endif

#if REDC_TYPE == VAR_RC
    , const wide_t q_prime
#endif

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == AVAR)
    , const wide_t field_a
#endif

);

#endif /* _POINT_ADD_H_ */
