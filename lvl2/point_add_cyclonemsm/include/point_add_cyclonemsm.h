#ifndef _POINT_ADD_CYCLONEMSM_H
#define _POINT_ADD_CYCLONEMSM_H

#include "primitives.h"
#include "modops.h"

EC_point_EP point_add_cyclonemsm(
    EC_point_EP P0, EC_point_EA P1 

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
);

#endif /* _POINT_ADD_CYCLONEMSM_H */
