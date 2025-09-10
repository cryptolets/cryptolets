#ifndef _MODADD_H_
#define _MODADD_H_

#include "primitives.h"

wide_t modadd_core(const wide_t a, const wide_t b, const wide_t q);
wide_t moddouble_core(const wide_t a, const wide_t q);

#if Q_TYPE == FIXED_Q
// Public API for fixed Q
wide_t modadd(const wide_t a, const wide_t b);
wide_t moddouble(const wide_t a);
#else
// Public API for variable Q
wide_t modadd(const wide_t a, const wide_t b, const wide_t q);
wide_t moddouble(const wide_t a, const wide_t q);
#endif

#endif /* _MODADD_H_ */
