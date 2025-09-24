# For Short Weierstrass curve = "point_add" kernel
# Sweep parameters
set BITWIDTHS {64} ;# 8 12 16 24 32 48 64 96 128 192 256 384 512 768 1024
set TECH_TYPES {gf12} ;# 45nm gf12 saed32 fpga
set TARGET_IIS {1}
set MUL_TYPES {nor} ;# kar sb nor
set TARGET_PERIODS {1} ;# in ns
set Q_TYPES {fixedq varq} ;# fixedq varq

# curve types: 
# RAND_CURVE
# a=0 : BN254 BLS12_377 BLS12_381 SECP256K1
# a=2 : MNT4753
# a=-3 : P_256 P_521
set CURVE_TYPES {RAND_CURVE}

# for RAND_CURVE can select what "a" to pick which will specify what formula will be used
# for other CURVE_TYPE's this value will be overrided
set FIELD_AS {A0 A2 ANEG3 AVAR} ;# A0: a=0, A2: a=2, ANEG3: a=-3, AVAR: variable a

set BASE_MUL_DEPTH_MAP {
    8 {8}
    12 {12}
    16 {16}
    24 {24}
    32 {32}
    48 {48}
    64 {64}
    96 {48}
    128 {64}
    192 {48}
    254 {63}
    255 {63}
    256 {64}
    381 {47}
    384 {48}
    377 {47}
    448 {56}
    512 {64}
    521 {65}
    753 {47}
    768 {48}
    1024 {64}
}

set KAR_MUL_DEPTH_MAP {
    8 {8}
    12 {12}
    16 {8}
    24 {12}
    32 {16}
    48 {24}
    64 {32}
    96 {48 24}
    128 {64 32}
    192 {96 48 24}
    254 {127 63}
    256 {128 64}
    377 {188 94 47}
    381 {190 95 47}
    384 {192 96 48}
    448 {224 112 56}
    512 {256 128 64}
    521 {260 130 65}
    753 {376 188 94 47}
    768 {384 192 96 48}
    1024 {512 256 128 64}
}

# DO NOT CHANGE UNLESS DEVELEOPMENT
# defines for order of params before project split (at the level we parallelize)
set SWEEPS_PROJ_ORDER {CURVE_TYPES FIELD_AS Q_TYPES TECH_TYPES MUL_TYPES TARGET_PERIODS TARGET_IIS BITWIDTHS BASE_MUL_DEPTH_MAP KAR_MUL_DEPTH_MAP}

# Control flags
set SIM true ;# verify RTL
set SYN false
set TEST true ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set HAS_MODSQ true ;# only false for cyclonemsm twisted edward formula so far
set CCORE_MUL_F false ;# make mul_f ccore, false = more compile time, better design latency  
set CCORE_MODADDSUB false ;# make modadd,modsub,moddouble ccore, false = more compile time, better design latency

# Note: we cannot set CCORE_TOP = true and SIM=true or TEST=true at the same time