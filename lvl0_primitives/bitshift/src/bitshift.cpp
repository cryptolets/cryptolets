#include "bitshift.h"

wide_t bitshift(
    const wide_t x,
    const int k
) {
#if BITSHIFT_DIRECTION == BITSHIFT_LEFT
    return x << k;
#elif BITSHIFT_DIRECTION == BITSHIFT_RIGHT
    return x >> k;
#endif
}