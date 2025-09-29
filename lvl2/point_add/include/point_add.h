#ifndef _POINT_ADD_H_
#define _POINT_ADD_H_

#include "primitives.h"
#include "modops.h"

#if Q_TYPE == FIXED_Q
    EC_point_J point_add(
        EC_point_J P0, EC_point_J P1
    );
#else // Q_TYPE == VAR_Q
    #if FIELD_A == AVAR
        EC_point_J point_add(
            EC_point_J P0, EC_point_J P1, 
            const wide_t q, const wide_t q_prime,
            const wide_t field_a
        );
    #else
        EC_point_J point_add(
            EC_point_J P0, EC_point_J P1, 
            const wide_t q, const wide_t q_prime
        );
    #endif
#endif


#endif /* _POINT_ADD_H_ */
