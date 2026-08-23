#ifndef _L0_INT_CMUL_H_
#define _L0_INT_CMUL_H_

#include <ac_int.h>
#include "params.h"

// Constant multiplier (cmul) implementation with different constants
// that are used by higher-level cryptographic kernels.

// The generated top copies the port types, so the widths need their own name
template<class _FIELD, int _CMUL_CONST>
struct l0_int_cmul_ports {
    // Barrett takes a double width x, Montgomery keeps only the low half.
    // A curve coefficient is an ordinary field element, so it keeps the whole
    // product for the reduction that follows.
    static constexpr int IN  = (_CMUL_CONST == CMUL_MU)      ? 2*_FIELD::W : _FIELD::W;
    static constexpr int OUT = (_CMUL_CONST == CMUL_Q_PRIME
                             || _CMUL_CONST == CMUL_MU)      ? _FIELD::W : 2*_FIELD::W;
};

template<class _FIELD, int _CMUL_CONST = CMUL_CONST>
class l0_int_cmul_impl {
    typedef l0_int_cmul_ports<_FIELD, _CMUL_CONST> ports;
    static constexpr int W = _FIELD::W;

public:
    void run(
        const ac_int<l0_int_cmul_ports<_FIELD,_CMUL_CONST>::IN, false> x,
        ac_int<l0_int_cmul_ports<_FIELD,_CMUL_CONST>::OUT, false> &z
    ) {
        if constexpr (_CMUL_CONST == CMUL_Q) {
            z = x * _FIELD::Q();                                   // whole product
        } else if constexpr (_CMUL_CONST == CMUL_Q_PRIME) {
            z = (x * _FIELD::Q_PRIME()).template slc<ports::OUT>(0);   // low half
        } else if constexpr (_CMUL_CONST == CMUL_MU) {
            z = (x * _FIELD::MU()).template slc<ports::OUT>(2*W);      // high half
        } else if constexpr (_CMUL_CONST == CMUL_A) {
            z = x * _FIELD::A();
        } else if constexpr (_CMUL_CONST == CMUL_B) {
            z = x * _FIELD::B();
        } else if constexpr (_CMUL_CONST == CMUL_D) {
            z = x * _FIELD::D();
        } else { // CMUL_K
            z = x * _FIELD::K();
        }
    }
};

#endif /* _L0_INT_CMUL_H_ */
