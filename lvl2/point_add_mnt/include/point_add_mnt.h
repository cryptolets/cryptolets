#ifndef _POINT_ADD_MNT_H_
#define _POINT_ADD_MNT_H_

#include "primitives.h"
#include "modadd.h"
#include "modsub.h"
#include "modmul_mont.h"

#if Q_TYPE == FIXED_Q

EC_point_J point_add_mnt(
    EC_point_J P0, EC_point_J P1
);

#else  // VARIABLE Q

EC_point_J point_add_mnt(
    EC_point_J P0, EC_point_J P1,
    const wide_t q, const wide_t q_prime
);

#endif

#endif /* _POINT_ADD_MNT_H_ */
