# Sweep parameters
set BITWIDTHS {384} ;# 8 12 16 24 32 48 64 96 128 192 256 384 512 768 1024
set TECH_TYPES {saed32} ;# 45nm gf12 saed32 fpga
set TARGET_IIS {1}
set MUL_TYPES {kar sb} ;# kar sb nor
set TARGET_PERIODS {4} ;# in ns
set Q_TYPES {varq fixedq} ;# in ns
set CURVE_TYPES {RAND_CURVE BN128}

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
    768 {48}
    1024 {64}
}

set KAR_MUL_DEPTH_MAP {
    8 {8}
    12 {12}
    16 {16}
    24 {24}
    32 {32 16}
    48 {48 24}
    64 {64 32 16}
    96 {96 48 24}
    128 {128 64 32 16}
    192 {192 96 48 24}
    254 {127 63}
    256 {64}
    377 {377 188 94 47}
    381 {381 190 95 47}
    384 {48}
    512 {512 256 128}
    521 {521 260 130 65}
    768 {768 384 192 96 48 23}
    1024 {1024 512 256 128 64 32 16}
}

# DO NOT CHANGE UNLESS DEVELEOPMENT
# defines for order of params before project split (at the level we parallelize)
set SWEEPS_PROJ_ORDER {CURVE_TYPES Q_TYPES TECH_TYPES MUL_TYPES TARGET_PERIODS TARGET_IIS BITWIDTHS BASE_MUL_DEPTH_MAP KAR_MUL_DEPTH_MAP}

# Control flags
set SIM false ;# verify RTL
set SYN true ;# run synthesis
set TEST true ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set CCORE_TOP false ;# gives us better area/latency for combination units
set CCORE_MUL_F false ;# make mul_f ccore, false = more compile time, better design latency  

# Note: we cannot set CCORE_TOP = true and SIM=true or TEST=true at the same time