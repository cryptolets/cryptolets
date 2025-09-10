#include "cmul_f.h"

wide_t cmul_f(const wide_t a) {
    return (a * Q_PRIME).slc<BITWIDTH>(0);
};
