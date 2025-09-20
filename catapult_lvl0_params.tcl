# Sweep parameters
set BITWIDTHS {256 384 768 1024}
set TECH_TYPES {gf12} ;# 45nm gf12 saed32 fpga
set TARGET_IIS {1}
set TARGET_PERIODS {1} ;# in ns

# DO NOT CHANGE UNLESS DEVELEOPMENT
# defines for order of params before project split (at the level we parallelize)
set SWEEPS_PROJ_ORDER {TECH_TYPES TARGET_PERIODS TARGET_IIS BITWIDTHS}

# Control flags
set SIM false ;# verify RTL
set SYN false
set TEST false ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set CCORE_TOP true ;# gives us better area/latency for combination units

# Note: we cannot set CCORE_TOP = true and SIM=true or TEST=true at the same time