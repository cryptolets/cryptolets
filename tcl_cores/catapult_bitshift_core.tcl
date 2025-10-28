# Sweep script for bitshift
set LVL_DIR "lvl0_primitives"
set ROOT_DIR [file normalize [file join [file dirname [info script]] ..]]
source [file join $ROOT_DIR utils util.tcl] ;# Import utilities

# parameter names
set config_params {TECH_TYPE TARGET_PERIOD TARGET_II BITWIDTH BITSHIFT_DIRECTION}
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
directive set -PIPELINE_INIT_INTERVAL $TARGET_II
directive set -DESIGN_GOAL latency
directive set -CCORE_TYPE sequential
directive set -OUTPUT_REGISTERS false
go compile

run_osci_test "" "" $BITSHIFT_DIRECTION
if {$TEST_ONLY} { exit 0 }

set_tech_lib $TECH_TYPE ;# set libraries
go libraries

set_clock $TARGET_PERIOD
go assembly

go schedule

extract_verify_syn_save