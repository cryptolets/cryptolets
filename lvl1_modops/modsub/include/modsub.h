#ifndef _MODSUB_H
#define _MODSUB_H

#include "primitives.h"

wide_t modsub_core(const wide_t a, const wide_t b, const wide_t q);

#if Q_TYPE == FIXED_Q
// Public API for fixed Q
wide_t modsub(const wide_t a, const wide_t b);
#else
// Public API for variable Q
wide_t modsub(const wide_t a, const wide_t b, const wide_t q);
#endif

#endif /* _MODSUB_H */
