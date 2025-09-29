#ifndef _POINT_ADD_H_
#define _POINT_ADD_H_

#include "primitives.h"
#include "modadd.h"
#include "modsub.h"
#include "modmul_mont.h"

EC_point_J point_add(
    EC_point_J P0, EC_point_J P1
#if Q_TYPE != FIXED_Q
    , const wide_t q, const wide_t q_prime
#endif
#if (Q_TYPE == VAR_Q && FIELD_A == AVAR)
    , const wide_t field_a
#endif
);

#endif /* _POINT_ADD_H_ */
