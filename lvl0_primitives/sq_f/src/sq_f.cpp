#include "sq_f.h"

#if PRECISION_MODE == PREC_SINGLE

wide_2x_t sq_f(
    const wide_t a
) {
    return sq_f_gen<BITWIDTH>(a);
}

#else // PREC_MULTI

// TODO:
wide_2x_t sq_f(
    const wide_t a
) {
    return mul_f(a, a);
}

#endif
