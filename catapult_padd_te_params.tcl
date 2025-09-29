# For Short Weierstrass curve = "point_add" kernel
# Sweep parameters
set BITWIDTHS {64 96} ;# 8 12 16 24 32 48 64 96 128 192 256 384 512 768
# 256 377 381 384
# 64 96 128 192 254 256 377 381 384 : clock 1ns and mod_ops_period ratio = 0.95
# 448 512 521 : clock at 1.1 and mod_ops_period ratio = 0.90
# 753 768 : 1.4 and mod_ops_period ratio = 0.90

set TECH_TYPES {gf12} ;# 45nm gf12 saed32 fpga
set TARGET_IIS {1}
set MUL_TYPES {nor} ;# kar sb nor
set TARGET_PERIODS {1} ;# in ns
set Q_TYPES {fixedq varq} ;# fixedq varq

# curve types: 
# RAND_CURVE
# a=-1 : ED25519 ED_384_MONT ED_511_MERS ED_512_MONT MNT4753_ED (BLS12_377_ED doesn't work - wrong params)
# variable 1 = ED448
set CURVE_TYPES {ED25519 ED448 ED_384_MONT RAND_CURVE}

# for RAND_CURVE can select what "a" to pick which will specify what formula will be used
# for other CURVE_TYPE's this value will be overrided
set FIELD_AS {ANEG1 AVAR} ;# ANEG1: a=-1, AVAR: variable a

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
    511 {63}
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
    192 {96 48}
    254 {127 63}
    255 {127 63}
    256 {128 64}
    377 {188 94 47}
    381 {190 95 47}
    384 {192 96 48}
    448 {224 112 56}
    511 {255 127 63}
    512 {256 128 64}
    521 {260 130 65}
    753 {376 188 94 47}
    768 {384 192 96 48}
    1024 {512 256 128 64}
}

# # FPGA - DSP 27 mul
# set BASE_MUL_DEPTH_MAP {
#     8 {8}
#     12 {12}
#     16 {16}
#     24 {24}
#     32 {16}
#     48 {24}
#     64 {16}
#     96 {24}
#     128 {16}
#     192 {24}
#     254 {15}
#     255 {15}
#     256 {16}
#     381 {23}
#     384 {24}
#     377 {23}
#     448 {14}
#     512 {16}
#     521 {16}
#     753 {23}
#     768 {24}
#     1024 {16}
# }

# # FPGA
# set KAR_MUL_DEPTH_MAP {
#     32 {16}
#     48 {24}
#     64 {32 16}
#     96 {48 24}
#     128 {64 32 16}
#     192 {96 48 24}
#     254 {127 63 31 15}
#     256 {128 64 32 16}
#     377 {188 94 47 23}
#     381 {190 95 47 23}
#     384 {192 96 48 24}
#     448 {224 112 56 28 14}
#     512 {256 128 64 32 16}
#     521 {260 130 65 32 16}
#     753 {376 188 94 47 23}
#     768 {384 192 96 48 24}
#     1024 {512 256 128 64 32 16}
# }

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
set HAS_MODSQ false ;# has to be false for twisted edward formulas so far
set CCORE_MUL_F false ;# make mul_f ccore, false = more compile time, better design latency  
set CCORE_MODADDSUB false ;# make modadd,modsub,moddouble ccore, false = more compile time, better design latency

# Note: we cannot set CCORE_TOP = true and SIM=true or TEST=true at the same time
