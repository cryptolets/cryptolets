# Sweep script for bw group (add_f, sub_f, cmul_f)
set LVL_DIR "lvl0_primitives"
set ROOT_DIR [file normalize [file join [file dirname [info script]] ..]]
source [file join $ROOT_DIR utils util.tcl] ;# Import utilities

# parameter names
set config_params {PREC_TYPE TECH_TYPE TARGET_PERIOD TARGET_II BITWIDTH WBW MASK_BITS}
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
set CURVE_TYPE ""
set json_file ""

set KERNEL_DIR [file join $ROOT_DIR $LVL_DIR $KERNEL_NAME]
set WORK_DIR [enter_work_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"
assert {!($CCORE_TOP && $PREC_TYPE eq "MULTI_PREC")} "top cannot be ccore for multi-precision"

set TEST [expr {$SIM || $TEST}]
set CCORE_TOP [expr {$CCORE_TOP && $TARGET_II <= 1}]

override_default_options ;# Reset tool options

set proj_name "Catapult_${SWEEP_KEY}"
set table_name "table_${SWEEP_KEY}.csv"
set sol_name $KERNEL_NAME

open_or_create_proj $proj_name
puts "\n=== Starting project $proj_name ==="

# Compiler flags
set flags ""
if {$KERNEL_NAME eq "cmul_f"} {
    set CURVE_TYPE "RAND_CURVE"
    set json_file [gen_field_consts] 
    append flags " -DQ_TYPE=FIXED_Q" 
}
puts "JSON FILE = $json_file"
set tmp_params_h_dir [gen_tmp_params_h $config_params $json_file $CURVE_TYPE]

open_or_create_solution $sol_name
puts "  -> Opening solution: $sol_name"

set include_dirs {
    utils/include
}
lappend include_dirs [file join $LVL_DIR $KERNEL_NAME include]
lappend include_dirs [file join $tmp_params_h_dir]
set include_flags [build_include_flags $include_dirs]

options set /Input/CompilerFlags "$flags $include_flags"

# Add kernel + dependencies
solution file add $KERNEL_DIR/src/${KERNEL_NAME}.cpp
solution file add $KERNEL_DIR/src/${KERNEL_NAME}_tb.cpp -exclude true
solution file add [file join $ROOT_DIR utils/src/csvparser.cpp] -exclude true
go analyze

# Set design tops
solution design set $KERNEL_NAME -top
if {$CCORE_TOP} {
    solution design set $KERNEL_NAME -ccore 
    directive set -CCORE_TYPE sequential
    directive set -OUTPUT_REGISTERS false
}
go compile

run_osci_test $CURVE_TYPE
if {$TEST_ONLY} { exit 0 }

set_tech_lib $TECH_TYPE ;# set libraries
go libraries

set_clock $TARGET_PERIOD
go assembly

if {$PREC_TYPE eq "SINGLE_PREC"} {
    directive set -PIPELINE_INIT_INTERVAL $TARGET_II
}
directive set -DESIGN_GOAL latency
go schedule

if {$CCORE_TOP} { branch_if_ccore_comb $KERNEL_NAME }

go extract
project save
solution table export -file [file join $WORK_DIR $table_name]
run_scverify
run_syn $TECH_TYPE

solution table export -file [file join $WORK_DIR $table_name]
project save