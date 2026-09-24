# Sweep script for ntt
set LVL_DIR "lvl2"
set ROOT_DIR [file normalize [file join [file dirname [info script]] ..]]
source [file join $ROOT_DIR utils util.tcl] ;# Import utilities

# parameter names
set config_params {
    MODMUL_TYPE CURVE_TYPE REDC_TYPE Q_TYPE PREC_TYPE TECH_TYPE TARGET_PERIOD
    CCORE_PERIOD_RATIO MUL_TYPE CMUL_TYPE TARGET_II BITWIDTH WBW
    BASE_MUL_WIDTH KAR_BASE_MUL_WIDTH
    NTT_LEN NTT_IMPL
    NTT_BF_UNROLL
}

if {[info exists env(NTT_IMPL)]} {
    if {$env(NTT_IMPL) eq "NTT_IMPL_STANDARD"} {
        lappend config_params NTT_STANDARD_VARIANT
    } elseif {$env(NTT_IMPL) eq "NTT_IMPL_CONSTANT_GEOMETRY"} {
        lappend config_params NTT_CONSTANT_GEOMETRY_VARIANT
    } elseif {$env(NTT_IMPL) eq "NTT_IMPL_STOCKHAM"} {
        lappend config_params NTT_STOCKHAM_VARIANT
    }
} else {
    lappend config_params NTT_STANDARD_VARIANT NTT_CONSTANT_GEOMETRY_VARIANT NTT_STOCKHAM_VARIANT
}
assign_from_env $config_params
set NTT_INTERLEAVE_FACTOR $NTT_BF_UNROLL

# control flags
set SIM $env(SIM)
set SYN $env(SYN)
set TEST $env(TEST)
set TEST_ONLY $env(TEST_ONLY)
set NUM_TEST_SAMPLES $env(NUM_TEST_SAMPLES)
set CCORE_TOP $env(CCORE_TOP)
set USE_CLUSTERS $env(USE_CLUSTERS)

# run config
set THREADS_PER_PROCESS $env(THREADS_PER_PROCESS)
set KERNEL_NAME $env(KERNEL_NAME)
set RTL_FILE $env(RTL_FILE)

set SWEEP_KEY $env(SWEEP_KEY)

set KERNEL_DIR [file join $ROOT_DIR $LVL_DIR $KERNEL_NAME]
set WORK_DIR [enter_work_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

assert {!($CCORE_TOP && $PREC_TYPE eq "MULTI_PREC")} "top cannot be ccore for multi-precision"

set TEST [expr {$SIM || $TEST}]
set CCORE_TOP [expr {$CCORE_TOP && $TARGET_II <= 1}]

override_default_options ;# Reset tool options

set proj_name "Catapult_${SWEEP_KEY}"
set table_name "table_${SWEEP_KEY}.csv"
set sol_name $KERNEL_NAME

open_or_create_proj $proj_name
puts "\n=== Starting project $proj_name ==="

del_existing_table $table_name

set json_file ""
set tmp_params_h_dir [gen_tmp_params_h $config_params $json_file ""]

solution rename "test_only_$sol_name"
puts "  -> Opening solution: $sol_name"

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
    lvl0_primitives/cmul_f/include
    lvl1_modops/modadd/include
    lvl1_modops/modsub/include
    lvl1_modops/include
    lvl1_modops/modmul_mont/include
    lvl1_modops/modmul_barrett/include
}

lappend include_dirs [file join $LVL_DIR $KERNEL_NAME include]
lappend include_dirs [file join $tmp_params_h_dir]
set include_flags [build_include_flags $include_dirs]
options set /Input/CompilerFlags "$include_flags"

# Add kernel + dependencies
solution file add $KERNEL_DIR/src/${KERNEL_NAME}.cpp
solution file add $KERNEL_DIR/src/ntt_common.cpp
solution file add $KERNEL_DIR/src/ntt_standard.cpp
solution file add $KERNEL_DIR/src/ntt_constant_geometry.cpp
solution file add $KERNEL_DIR/src/ntt_stockham.cpp
solution file add $KERNEL_DIR/src/${KERNEL_NAME}_tb.cpp -exclude true
solution file add [file join $ROOT_DIR utils/src/csvparser.cpp] -exclude true
solution file add [file join $ROOT_DIR lvl0_primitives/mul_f/src/mul_f.cpp]
solution file add [file join $ROOT_DIR lvl0_primitives/sq_f/src/sq_f.cpp]
solution file add [file join $ROOT_DIR lvl0_primitives/cmul_f/src/cmul_f.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modadd/src/modadd.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modsub/src/modsub.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modmul_mont/src/modmul_mont.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modmul_barrett/src/modmul_barrett.cpp]

go analyze
solution design set $KERNEL_NAME -top

if {$USE_CLUSTERS && ![is_fpga $TECH_TYPE]} {
    directive set -CLUSTER addtree
    directive set -CLUSTER_FAST_MODE true
}

go compile
run_osci_test "" $MODMUL_TYPE
if {$TEST_ONLY} { exit 0 }



# if {$CMUL_TYPE ne "CMUL_NORMAL"} {
#     directive set REGISTER_THRESHOLD [expr (8 * $BITWIDTH)]
# }


if {[is_fpga $TECH_TYPE]} {
    directive set DSP_EXTRACTION yes
    directive set DSP_EXTRACTION_TRAV_PREADD_FANOUT true
    directive set DSP_EXTRACTION_UNFOLD_MAC true
}

set_tech_lib $TECH_TYPE ;# set libraries
solution library add ccs_sample_mem

directive set /ntt/ping:rsc -MAP_TO_MODULE ccs_sample_mem.ccs_ram_sync_dualport
directive set /ntt/pong:rsc -MAP_TO_MODULE ccs_sample_mem.ccs_ram_sync_dualport
directive set /ntt/omegas:rsc -MAP_TO_MODULE ccs_sample_mem.ccs_ram_sync_1R1W

directive set /ntt/ping:rsc -INTERLEAVE $NTT_INTERLEAVE_FACTOR
directive set /ntt/pong:rsc -INTERLEAVE $NTT_INTERLEAVE_FACTOR
directive set /ntt/omegas:rsc -INTERLEAVE $NTT_INTERLEAVE_FACTOR


directive set -DESIGN_GOAL latency
directive set -CCORE_TYPE sequential
directive set -OUTPUT_REGISTERS false
directive set -OPT_CONST_MULTS full

go libraries

set_clock $TARGET_PERIOD

directive set /ntt/core/STAGE -UNROLL yes

# TODO: Reverse bits needs to be unrolled in the right spot
# directive set /ntt/core/STAGE -REVERSE_BITS yes
if {$NTT_IMPL eq "NTT_IMPL_CONSTANT_GEOMETRY"} {
    directive set /ntt/core/BF_COMPUTE -UNROLL $NTT_BF_UNROLL
    directive set /ntt/core/BF_COMPUTE -PIPELINE_INIT_INTERVAL 1
} elseif {$NTT_IMPL eq "NTT_IMPL_STOCKHAM"} {
    directive set /ntt/core/BF_COMPUTE -UNROLL $NTT_BF_UNROLL
    directive set /ntt/core/BF_COMPUTE -PIPELINE_INIT_INTERVAL 1
} else {
    directive set /ntt/core/OFFSET -UNROLL $NTT_BF_UNROLL
}



go assembly
go schedule

extract_verify_syn_save
if {![info exists env(GUI_MODE)] || $env(GUI_MODE) ne "true"} {
    exit 0
}
