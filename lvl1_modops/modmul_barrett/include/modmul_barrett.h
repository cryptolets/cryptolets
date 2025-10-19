#ifndef _MODMUL_MONT_H_
#define _MODMUL_MONT_H_

#include "primitives.h"
#include "mul_f.h"
#include "sq_f.h"

wide_t modmul_barrett_core(
    const wide_t x, const wide_t y,
    const wide_t q, const wide_2x_t mu
);

wide_t modsq_barrett_core(
    const wide_t x, 
    const wide_t q, const wide_2x_t mu
);


// special case where we are multiplying by a const
#ifdef FIELD_A_HEX
    wide_t cmodmul_a_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu);
#endif

#ifdef FIELD_D_HEX
    wide_t cmodmul_d_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu);
#endif

#ifdef FIELD_K_HEX
    wide_t cmodmul_k_barrett_core(const wide_t x, const wide_t q, const wide_2x_t mu);
#endif

wide_t modmul_barrett(
    const wide_t x, const wide_t y
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_2x_t mu
#endif
);

wide_t modsq_barrett(
    const wide_t x
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_2x_t mu
#endif
);

#endif /* _MODMUL_MONT_H_ */
