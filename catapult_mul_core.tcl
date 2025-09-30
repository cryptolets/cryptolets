# Sweep script for bw group (mul_f, sq_f)
set lvl_dir "lvl0_primitives"

# import project level sweep params from env
set tech_type $env(TECH_TYPE)
set period $env(TARGET_PERIOD)
set target_ii $env(TARGET_II)
set mul_type $env(MUL_TYPE)
set bitwidth $env(BITWIDTH)
set bm $env(BASE_MUL_DEPTH)
set kar $env(KAR_MUL_DEPTH)
set rtl_file $env(RTL_FILE)

set MAX_SYN_THREADS $env(DESIGN_COMPILER_THREADS)
set kernel $env(KERNEL_NAME)
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]
source [file join $root_dir $env(PARAMS_TCL_SCRIPT)] ;# get solution level params and control flags

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

set TEST [expr {$SIM || $TEST}]
assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"
override_default_options ;# Reset tool options

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
}

lappend include_dirs [file join $lvl_dir $kernel include]
set include_flags [build_include_flags $root_dir $include_dirs]

set period_str [string map {. _} $period]
set sweep_key "bw${bitwidth}_tt${tech_type}_ii${target_ii}_mt${mul_type}_bm${bm}_kar${kar}_p${period_str}ns"
set proj_name "Catapult_${sweep_key}"
open_or_create_proj $proj_name $work_dir
puts "\n=== Starting project $proj_name ==="

set sol_name "sol"
set table_name "table_${sweep_key}.csv"
set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

open_or_create_solution $sol_name
puts "  -> Solution: $sol_name (bitwidth=$bitwidth, bm=$bm, kar=$kar)"

# Compiler flags
set flags ""
append flags " -DBITWIDTH=$bitwidth"
append flags " -DMUL_TYPE=[get_mul_val $mul_type]"
append flags " -DKAR_BASE_MUL_WIDTH=$kar"
append flags " -DBASE_MUL_WIDTH=$bm"
options set /Input/CompilerFlags "$include_flags $flags"

# Add kernel + dependencies
solution file add $kernel_dir/src/${kernel}.cpp
solution file add $kernel_dir/src/${kernel}_tb.cpp -exclude true
solution file add [file join $root_dir utils/src/csvparser.cpp] -exclude true
go analyze

# Set design tops
solution design set $kernel -top
if {$CCORE_TOP} {
    solution design set $kernel -ccore 
    directive set -CCORE_TYPE sequential
    directive set -OUTPUT_REGISTERS false
}

go compile

run_osci_test $kernel_dir $work_dir $root_dir $bitwidth $NUM_TEST_SAMPLES $TEST $GEN_SAMPLES
if {$TEST_ONLY} { exit }

set_tech_lib $tech_type $root_dir ;# set libraries
go libraries

set_clock $period
go assembly

directive set -PIPELINE_INIT_INTERVAL $target_ii
directive set -DESIGN_GOAL latency
go architect

# Make sure mgc_mul's with blank MinClkPrd are not used
remove_broken_mul_libs $tech_type
go schedule

if {$CCORE_TOP} { branch_if_ccore_comb $kernel }

go extract
project save
solution table export -file [file join $work_dir $table_name]

run_scverify $kernel_dir $work_dir $bitwidth $SIM
run_syn $tech_type $SYN $root_dir $rtl_file
solution table export -file [file join $work_dir $table_name]

project save