# Sweep parameters
set BITWIDTHS {32 64 128 256}
set TECH_TYPES {asicgf12} ;# asic fpga asicgf12
set TARGET_IIS {1 2 4}
set TARGET_PERIODS {3 4} ;# in ns

# DO NOT CHANGE UNLESS DEVELEOPMENT
# defines for order of params before project split (at the level we parallelize)
set SWEEPS_PROJ_ORDER {TECH_TYPES TARGET_PERIODS TARGET_IIS BITWIDTHS}

# Control flags
set SIM true ;# verify RTL
set SYN false
set TEST true ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set CCORE_TOP false ;# gives us better area/latency for combination units

assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"