#ifndef _MODMUL_MONT_H_
#define _MODMUL_MONT_H_

#include "primitives.h"
#include "mul_f.h"
#include "sq_f.h"

wide_t modmul_mont_core(
    const wide_t x, const wide_t y,
    const wide_t q, const wide_t q_prime
);

wide_t modsq_mont_core(
    const wide_t x, 
    const wide_t q, const wide_t q_prime
);


// special case where we are multiplying by a const
#ifdef FIELD_A_MONT_HEX
    wide_t cmodmul_a_mont_core(const wide_t x, const wide_t q, const wide_t q_prime);
#endif

#ifdef FIELD_D_MONT_HEX
    wide_t cmodmul_d_mont_core(const wide_t x, const wide_t q, const wide_t q_prime);
#endif

#ifdef FIELD_K_MONT_HEX
    wide_t cmodmul_k_mont_core(const wide_t x, const wide_t q, const wide_t q_prime);
#endif

wide_t modmul_mont(
    const wide_t x, const wide_t y
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_t q_prime
#endif
);

wide_t modsq_mont(
    const wide_t x
#if Q_TYPE == VAR_Q
    , const wide_t q
#endif 

#if REDC_TYPE == VAR_RC
    , const wide_t q_prime
#endif
);

#endif /* _MODMUL_MONT_H_ */
