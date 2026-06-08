#include "sq_f.h"

#if PREC_TYPE == SINGLE_PREC

wide_2x_t sq_f(
    const wide_t a
) {
    return sq_f_gen<BITWIDTH>(a);
}

#elif PREC_TYPE == MULTI_PREC

// TODO:
wide_2x_t sq_f(
    const wide_t a
) {
    return mul_f(a, a);
}

#endif
