#ifndef _PRIMITIVES_H_
#define _PRIMITIVES_H_

#include "params.h"
#include "tmp_params.h"
#include <ac_int.h>

#ifdef PREC_TYPE
    #if PREC_TYPE == MULTI_PREC
        #define LIMBS (BITWIDTH / WBW)
        
        typedef ac_int<WBW,false>       word_t;
        typedef ac_int<WBW+1,false>     word_1_t;
        typedef ac_int<WBW+2,false>     word_2_t;
        typedef ac_int<WBW*2,false>     word_2x_t;
        typedef ac_int<(WBW*2)+1,false> word_2x_1_t;
        typedef ac_int<(WBW*2)+2,false> word_2x_2_t;
        typedef ac_int<WBW+1,true>      word_signed_t;
        typedef ac_int<WBW+2,true>      word_2_signed_t;
        typedef ac_int<(2*WBW)+1, true> word_2x_signed_t;
    #endif
#endif

typedef ac_int<BITWIDTH, false>         wide_t;
typedef ac_int<BITWIDTH+1, false>       wide_1_t;
typedef ac_int<BITWIDTH+2, false>       wide_2_t;
typedef ac_int<BITWIDTH*2, false>       wide_2x_t;
typedef ac_int<BITWIDTH*4, false>       wide_4x_t;
typedef ac_int<(BITWIDTH*2)+1, false>   wide_2x_1_t;
typedef ac_int<(BITWIDTH*2)+2, false>   wide_2x_2_t;
typedef ac_int<BITWIDTH+1, true>        wide_signed_t;
typedef ac_int<BITWIDTH+2, true>        wide_2_signed_t;
typedef ac_int<(2*BITWIDTH)+1, true>    wide_2x_signed_t;

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
#ifdef Q_HEX
    static const wide_t Q = ac::bit_fill_hex<wide_t>(Q_HEX);
    static const int Q_NAF[] = Q_NAF_ARR;
    static const int Q_NAF_LEN = sizeof(Q_NAF) / sizeof(Q_NAF[0]);
#endif

// Montgomery constant
#ifdef Q_PRIME_HEX
    static const wide_t Q_PRIME = ac::bit_fill_hex<wide_t>(Q_PRIME_HEX);
    static const int Q_PRIME_NAF[] = Q_PRIME_NAF_ARR;
    static const int Q_PRIME_NAF_LEN = sizeof(Q_PRIME_NAF) / sizeof(Q_PRIME_NAF[0]);
#endif

// Barrett constant
#ifdef MU_HEX
    static const wide_2x_t MU = ac::bit_fill_hex<wide_2x_t>(MU_HEX);
    static const int MU_NAF[] = MU_NAF_ARR;
    static const int MU_NAF_LEN = sizeof(MU_NAF) / sizeof(MU_NAF[0]);
#endif

// #ifdef CURVE_PARAMS_TYPE
// For Montgomery Modmul
#ifdef FIELD_A_MONT_HEX
    static const wide_t FIELD_A_MONT = ac::bit_fill_hex<wide_t>(FIELD_A_MONT_HEX);
    static const int FIELD_A_MONT_NAF[] = FIELD_A_MONT_NAF_ARR;
    static const int FIELD_A_MONT_NAF_LEN = sizeof(FIELD_A_MONT_NAF) / sizeof(FIELD_A_MONT_NAF[0]);
#endif

#ifdef FIELD_B_MONT_HEX
    static const wide_t FIELD_B_MONT = ac::bit_fill_hex<wide_t>(FIELD_B_MONT_HEX);
    static const int FIELD_B_MONT_NAF[] = FIELD_B_MONT_NAF_ARR;
    static const int FIELD_B_MONT_NAF_LEN = sizeof(FIELD_B_MONT_NAF) / sizeof(FIELD_B_MONT_NAF[0]);
#endif

#ifdef FIELD_D_MONT_HEX
    static const wide_t FIELD_D_MONT = ac::bit_fill_hex<wide_t>(FIELD_D_MONT_HEX);
    static const int FIELD_D_MONT_NAF[] = FIELD_D_MONT_NAF_ARR;
    static const int FIELD_D_MONT_NAF_LEN = sizeof(FIELD_D_MONT_NAF) / sizeof(FIELD_D_MONT_NAF[0]);
#endif

#ifdef FIELD_K_MONT_HEX
    static const wide_t FIELD_K_MONT = ac::bit_fill_hex<wide_t>(FIELD_K_MONT_HEX);
    static const int FIELD_K_MONT_NAF[] = FIELD_K_MONT_NAF_ARR;
    static const int FIELD_K_MONT_NAF_LEN = sizeof(FIELD_K_MONT_NAF) / sizeof(FIELD_K_MONT_NAF[0]);
#endif

// For Barrett Modmul
#ifdef FIELD_A_HEX
    static const wide_t FIELD_A_INT = ac::bit_fill_hex<wide_t>(FIELD_A_HEX);
    static const int FIELD_A_NAF[] = FIELD_A_NAF_ARR;
    static const int FIELD_A_NAF_LEN = sizeof(FIELD_A_NAF) / sizeof(FIELD_A_NAF[0]);
#endif

#ifdef FIELD_B_HEX
    static const wide_t FIELD_B_INT = ac::bit_fill_hex<wide_t>(FIELD_B_HEX);
    static const int FIELD_B_NAF[] = FIELD_B_NAF_ARR;
    static const int FIELD_B_NAF_LEN = sizeof(FIELD_B_NAF) / sizeof(FIELD_B_NAF[0]);
#endif

#ifdef FIELD_D_HEX
    static const wide_t FIELD_D_INT = ac::bit_fill_hex<wide_t>(FIELD_D_HEX);
    static const int FIELD_D_NAF[] = FIELD_D_NAF_ARR;
    static const int FIELD_D_NAF_LEN = sizeof(FIELD_D_NAF) / sizeof(FIELD_D_NAF[0]);
#endif

#ifdef FIELD_K_HEX
    static const wide_t FIELD_K_INT = ac::bit_fill_hex<wide_t>(FIELD_K_HEX);
    static const int FIELD_K_NAF[] = FIELD_K_NAF_ARR;
    static const int FIELD_K_NAF_LEN = sizeof(FIELD_K_NAF) / sizeof(FIELD_K_NAF[0]);
#endif

// #endif

#endif // _PRIMITIVES_H_
