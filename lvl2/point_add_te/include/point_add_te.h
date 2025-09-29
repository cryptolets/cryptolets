#ifndef _POINT_ADD_TE_H_
#define _POINT_ADD_TE_H_

#include "primitives.h"
#include "modadd.h"
#include "modsub.h"
#include "modmul_mont.h"

EC_point_EP point_add_te(
    EC_point_EP P0, EC_point_EP P1
#if Q_TYPE == VAR_Q
    , const wide_t q, const wide_t q_prime
#if (FIELD_A == ANEG1)
    , const wide_t field_k
#endif
#if (FIELD_A == AVAR)
    , const wide_t field_a, const wide_t field_d
#endif
#endif
);

#endif /* _POINT_ADD_TE_H_ */
