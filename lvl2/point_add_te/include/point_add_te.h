#ifndef _POINT_ADD_TE_H_
#define _POINT_ADD_TE_H_

#include "primitives.h"
#include "modops.h"


#if Q_TYPE == FIXED_Q
    EC_point_EP point_add_te(
        EC_point_EP P0, EC_point_EP P1
    );
#else // Q_TYPE == VAR_Q
    #if FIELD_A == ANEG1
        EC_point_EP point_add_te(
            EC_point_EP P0, EC_point_EP P1, 
            const wide_t q, const wide_t q_prime,
            const wide_t field_k
        );
    #elif FIELD_A == AVAR
        EC_point_EP point_add_te(
            EC_point_EP P0, EC_point_EP P1, 
            const wide_t q, const wide_t q_prime,
            const wide_t field_a, const wide_t field_d
        );
    #else
        EC_point_EP point_add_te(
            EC_point_EP P0, EC_point_EP P1,
            const wide_t q, const wide_t q_prime
        );
    #endif
#endif

#endif /* _POINT_ADD_TE_H_ */
