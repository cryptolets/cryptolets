#ifndef _PARAMS_H_
#define _PARAMS_H_

// -------------------------------------------------------------------
// Precision mode
// -------------------------------------------------------------------
#define PREC_SINGLE 0
#define PREC_MULTI  1

#ifndef PRECISION_MODE
  #define PRECISION_MODE PREC_SINGLE
#endif

#ifndef BITWIDTH
  #define BITWIDTH 64   // default bitwidth
#endif

#if PRECISION_MODE == PREC_MULTI
  #ifndef LIMBS
    #define LIMBS 4       // number of limbs
  #endif
  #define WBW (BITWIDTH / LIMBS) // word bitwidth
#endif

// -------------------------------------------------------------------
// Base Multiplier Config
// -------------------------------------------------------------------
#define MUL_NORMAL     0
#define MUL_KARATSUBA  1
#define MUL_SCHOOLBOOK 2

#ifndef MUL_TYPE
  #define MUL_TYPE MUL_NORMAL
#endif

// bitwidth for schoolbook or karatsuba, where it will stop decomposing and use normal mul
// For FPGA, this largely defined by how well the specific DSP handles a certian bitwidth (27-bit)
// For ASIC, this is defined by what max bitwidth there is a highly optimized mul lib (128-bit)
#ifndef BASE_MUL_WIDTH
  #define BASE_MUL_WIDTH 32
#endif

// how many times to use karatsuba decomp, before using schoolbook (from topdown)
#ifndef KAR_BASE_MUL_WIDTH
  #define KAR_BASE_MUL_WIDTH 32
#endif

// Inline whole mul funcs by default
#ifndef CCORE_MULS
  #define CCORE_MULS 0
#endif

// --- MOD SPECIFIC PARAMS ---
// Define if we want fixed q prime with const muls or not
#define FIXED_Q 0
#define VAR_Q   1

#ifndef Q_TYPE
#define Q_TYPE VAR_Q
#endif

// -------------------------------------------------------------------
// Point Addition Curve Config
// -------------------------------------------------------------------
// Short Weierstrass
#define RAND_CURVE 0
#define BN128 1
#define SECP256K1 2
#define BLS12_377 3
#define BLS12_381 4

// Differential add
#define CURVE25519 8
#define CURVE448 9

// Twisted Edwards
#define ED25519 10
#define ED448 11

#ifndef CURVE_TYPE
  #define CURVE_TYPE RAND_CURVE
#endif

// Assumptions about a
#define A0 0 // a=0
#define A2 2 // a=2
#define ANEG3 3 // a=-3
#define AVAR 4 // variable a

#ifndef FIELD_A
#define FIELD_A A_0
#endif

#endif // _PARAMS_H_
