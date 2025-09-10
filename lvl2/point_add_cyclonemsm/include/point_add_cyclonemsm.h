#ifndef _POINT_ADD_CYCLONEMSM_H
#define _POINT_ADD_CYCLONEMSM_H

#include "primitives.h"
#include "modadd.h"
#include "modsub.h"
#include "modmul_mont.h"

#if Q_TYPE == FIXED_Q

EC_point_EP point_add_cyclonemsm(
    EC_point_EP P0, 
    EC_point_EA P1
);

#else  // VARIABLE Q

EC_point_EP point_add_cyclonemsm(
    EC_point_EP P0, 
    EC_point_EA P1,
    const wide_t q, const wide_t q_prime
);

#endif

#endif /* _POINT_ADD_CYCLONEMSM_H */
