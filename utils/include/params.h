#ifndef _PARAMS_H_
#define _PARAMS_H_

// -------------------------------------------------------------------
// Precision mode
// -------------------------------------------------------------------
#define SINGLE_PREC 0
#define MULTI_PREC  1

// -------------------------------------------------------------------
// Base Multiplier Config
// -------------------------------------------------------------------
#define MUL_NORMAL     0
#define MUL_KARATSUBA  1
#define MUL_SCHOOLBOOK 2

// Const Multiplier Type
#define CMUL_NORMAL 0
#define CMUL_NAF 1
#define CMUL_SA 2

// --- MOD SPECIFIC PARAMS ---
// Define if we want fixed q prime with const muls or not
#define FIXED_Q 0
#define VAR_Q   1

#define FIXED_RC 0
#define VAR_RC   1

// Modmul type
#define MODMUL_TYPE_MONT 0
#define MODMUL_TYPE_BARRETT 1

// -------------------------------------------------------------------
// Point Addition Curve Config
// -------------------------------------------------------------------
// Assumptions about a
#define A0 0     // a=0
#define ANEG1 1  // a=-1
#define A2 2     // a=2
#define ANEG3 3  // a=-3
#define AVAR 4   // variable a

// Fixed or Variable Curve Params
#define FIXED_CURVE_PARAMS 0
#define VAR_CURVE_PARAMS 1

// Bitshift
#define BITSHIFT_LEFT 0
#define BITSHIFT_RIGHT 1

#endif // _PARAMS_H_
