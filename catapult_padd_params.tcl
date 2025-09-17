# Sweep parameters
set BITWIDTHS {64} ;# 8 12 16 24 32 48 64 96 128 192 256 384 512 768 1024
set TECH_TYPES {gf12} ;# 45nm gf12 saed32 fpga
set TARGET_IIS {1}
set MUL_TYPES {sb} ;# kar sb nor
set TARGET_PERIODS {3} ;# in ns
set Q_TYPES {varq} ;# in ns
set CURVE_TYPES {BN128}

set base_mul_depth_map {
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

set kar_mul_depth_map {
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
    256 {256 128 64 32}
    384 {384 192 96}
    512 {512 256 128}
    521 {521 260 130 65}
    768 {768 384 192 96 48 23}
    1024 {1024 512 256 128 64 32 16}
}

# DO NOT CHANGE UNLESS DEVELEOPMENT
# defines for order of params before project split (at the level we parallelize)
set SWEEPS_PROJ_ORDER {CURVE_TYPES Q_TYPES TECH_TYPES MUL_TYPES TARGET_PERIODS TARGET_IIS BITWIDTHS}

# Control flags
set SIM false ;# verify RTL
set SYN false
set TEST true ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set HAS_MODSQ true ;# only false for cyclonemsm twisted edward formula so far

# Note: we cannot set CCORE_TOP = true and SIM=true or TEST=true at the same time