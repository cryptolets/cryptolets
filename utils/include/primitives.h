#ifndef _PRIMITIVES_H_
#define _PRIMITIVES_H_

#include "params.h"
#include <ac_int.h>

typedef ac_int<BITWIDTH, false>         wide_t;
typedef ac_int<BITWIDTH+1, false>       wide_1_t;
typedef ac_int<BITWIDTH*2, false>       wide_2x_t;
typedef ac_int<(BITWIDTH*2)+1, false>   wide_2x_1_t;
typedef ac_int<(BITWIDTH*2)+2, false>   wide_2x_2_t;
typedef ac_int<BITWIDTH+1, true>        wide_signed_t;

#if PRECISION_MODE == PREC_MULTI
typedef ac_int<WBW,false>       word_t;
typedef ac_int<WBW+1,false>     word_1_t;
typedef ac_int<WBW*2,false>     word_2x_t;
typedef ac_int<(WBW*2)+1,false> word_2x_1_t;
typedef ac_int<(WBW*2)+2,false> word_2x_2_t;
typedef ac_int<WBW+1,true>      word_signed_t;
#endif

// EC Points
// Affine coordinates
typedef struct {
    wide_t x;
    wide_t y;
} EC_point_A;


// Jacobian coordinates
typedef struct {
    wide_t X;
    wide_t Y;
    wide_t Z;
} EC_point_J;

// Extended Projective coordinates
typedef struct {
    wide_t X;
    wide_t Y;
    wide_t Z;
    wide_t T;
} EC_point_EP;

// Extended Affine coordinates
typedef struct {
    wide_t x;
    wide_t y;
    wide_t u;
} EC_point_EA;

// --- Fixed modulus values (for const-Q optimizations) ---
#if Q_TYPE == FIXED_Q
static const wide_t Q = ac::bit_fill_hex<wide_t>(Q_HEX);
static const wide_t Q_PRIME = ac::bit_fill_hex<wide_t>(Q_PRIME_HEX);
#endif

#endif // _PRIMITIVES_H_
