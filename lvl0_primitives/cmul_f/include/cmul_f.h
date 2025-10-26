#ifndef _CMUL_F_H_
#define _CMUL_F_H_

#include "primitives.h"

wide_t cmul_f(const wide_t a);

// -- For heigher level use --
// For modmul constant multiplications
wide_t cmul_q_prime(const wide_t x);
wide_2x_t cmul_q(const wide_t x);
wide_t cmul_mu(const wide_2x_t x);

// For field constant multiplications in montgomery domain
wide_2x_t cmul_field_a_mont(const wide_2x_t x);
wide_2x_t cmul_field_d_mont(const wide_2x_t x);
wide_2x_t cmul_field_k_mont(const wide_2x_t x);

// For field constant multiplications in normal domain (for barrett)
wide_2x_t cmul_field_a(const wide_2x_t x);
wide_2x_t cmul_field_d(const wide_2x_t x);
wide_2x_t cmul_field_k(const wide_2x_t x);

#endif /* _CMUL_F_H_ */
