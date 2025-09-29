# Sweep parameters
set BITWIDTHS {256} ;# 8 12 16 24 32 48 64 96 128 192 256 384 512 768 1024
set TECH_TYPES {gf12} ;# 45nm gf12 saed32 fpga
set TARGET_IIS {1}
set MUL_TYPES {nor} ;# kar sb nor
set TARGET_PERIODS {1} ;# in ns
set Q_TYPES {fixedq varq} ;# in ns

# curve types: 
# RAND_CURVE
# a=0 : BN254 BLS12_377 BLS12_381 SECP256K1
# a=2 : MNT4753
# a=-3 : P_256 P_521
set CURVE_TYPES {BN254}

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
    521 {260 65}
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
set SWEEPS_PROJ_ORDER {CURVE_TYPES Q_TYPES TECH_TYPES MUL_TYPES TARGET_PERIODS TARGET_IIS BITWIDTHS BASE_MUL_DEPTH_MAP KAR_MUL_DEPTH_MAP}

# Control flags
set SIM true ;# verify RTL
set SYN false ;# run synthesis
set TEST true ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set CCORE_TOP false ;# gives us better area/latency for combination units
set CCORE_MUL_F false ;# make mul_f ccore, false = more compile time, better design latency

# Note: we cannot set CCORE_TOP = true and SIM=true or TEST=true at the same time