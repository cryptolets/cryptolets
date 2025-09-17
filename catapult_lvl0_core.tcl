# Sweep script for bw group (add_f, sub_f, cmul_f)
set lvl_dir "lvl0_primitives"

# import project level sweep params from env
set tech_type $env(TECH_TYPE)
set period $env(TARGET_PERIOD)
set target_ii $env(TARGET_II)
set bitwidth $env(BITWIDTH)

set kernel $env(KERNEL_NAME)
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]
source [file join $root_dir catapult_lvl0_params.tcl] ;# get solution level params and control flags

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

override_default_options ;# Reset tool options

set include_dirs {
    utils/include
}
lappend include_dirs [file join $lvl_dir $kernel include]
set include_flags [build_include_flags $root_dir $include_dirs]

set period_str [string map {. _} $period]
set sweep_key "bw${bitwidth}_tt${tech_type}_ii${target_ii}_p${period_str}ns"
set proj_name "Catapult_${sweep_key}"
set table_name "table_${sweep_key}.csv"
set sol_name "sol"
set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

open_or_create_proj $proj_name $work_dir
puts "\n=== Starting project $proj_name ==="

set sol_name "sol"
open_or_create_solution $sol_name
puts "  -> Solution: $sol_name (bitwidth=$bitwidth)"

# Compiler flags
set flags ""
append flags " -DBITWIDTH=$bitwidth"
if {$kernel eq "cmul_f"} {
    append flags " -DQ_TYPE=FIXED_Q"
}
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
go schedule

if {$CCORE_TOP} { branch_if_ccore_comb $kernel }

go extract
solution table export -file [file join $work_dir $table_name]
run_scverify $kernel_dir $work_dir $bitwidth $SIM
run_syn $tech_type $SYN $root_dir
solution table export -file [file join $work_dir $table_name]
project save