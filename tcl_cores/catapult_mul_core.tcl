# Sweep script for bw group (mul_f, sq_f)
set LVL_DIR "lvl0_primitives"
set ROOT_DIR [file normalize [file join [file dirname [info script]] ..]]
source [file join $ROOT_DIR utils util.tcl] ;# Import utilities

# parameter names
set config_params {
    PREC_TYPE TECH_TYPE TARGET_PERIOD MUL_TYPE TARGET_II 
    BITWIDTH WBW MASK_BITS BASE_MUL_WIDTH KAR_BASE_MUL_WIDTH
}
assign_from_env $config_params

# control flags
set SIM $env(SIM)
set SYN $env(SYN)
set TEST $env(TEST)
set TEST_ONLY $env(TEST_ONLY)
set NUM_TEST_SAMPLES $env(NUM_TEST_SAMPLES)
set CCORE_TOP $env(CCORE_TOP)

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

set tmp_params_h_dir [gen_tmp_params_h $config_params]

solution rename "test_only_$sol_name"
puts "  -> Opening solution: $sol_name"

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
}

lappend include_dirs [file join $LVL_DIR $KERNEL_NAME include]
lappend include_dirs [file join $tmp_params_h_dir]
set include_flags [build_include_flags $include_dirs]
options set /Input/CompilerFlags "$include_flags"

# Add kernel + dependencies
solution file add $KERNEL_DIR/src/${KERNEL_NAME}.cpp
solution file add $KERNEL_DIR/src/${KERNEL_NAME}_tb.cpp -exclude true
solution file add [file join $ROOT_DIR utils/src/csvparser.cpp] -exclude true
go analyze

# Set design tops
solution design set $KERNEL_NAME -top
directive set -X_PHD_SYNTHESIS true

go compile
# directive set /$KERNEL_NAME -CLUSTER addtree

run_osci_test
if {$TEST_ONLY} { exit 0 }

if {$PREC_TYPE eq "SINGLE_PREC"} {
    directive set -PIPELINE_INIT_INTERVAL $TARGET_II
}
directive set -DESIGN_GOAL latency
directive set -CCORE_TYPE sequential
directive set -OUTPUT_REGISTERS false
set_tech_lib $TECH_TYPE ;# set libraries
go libraries

set_clock $TARGET_PERIOD
go architect

# Make sure mgc_mul's with blank MinClkPrd are not used
remove_broken_mul_libs $TECH_TYPE
go schedule

extract_verify_syn_save