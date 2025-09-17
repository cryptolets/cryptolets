# Sweep script for bw group (modadd, modsub)
set lvl_dir "lvl1_modops"
# import project level sweep params from env
set tech_type $env(TECH_TYPE)
set period $env(TARGET_PERIOD)
set target_ii $env(TARGET_II)
set bitwidth $env(BITWIDTH)
set q_type $env(Q_TYPE)
set curve_type $env(CURVE_TYPE)

set kernel $env(KERNEL_NAME)
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]
source [file join $root_dir catapult_lvl1_params.tcl] ;# get solution level params and control flags

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"
override_default_options ;# Reset tool options

set include_dirs {
    utils/include
}

lappend include_dirs [file join $lvl_dir $kernel include]
set include_flags [build_include_flags $root_dir $include_dirs]

set period_str [string map {. _} $period]
set sweep_key "bw${bitwidth}_tt${tech_type}_ii${target_ii}_qt${q_type}_p${period}ns_ct${curve_type}"
set proj_name "Catapult_${sweep_key}"
set table_name "table_$sweep_key.csv"
set sol_name "sol"
set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

open_or_create_proj $proj_name $work_dir
puts "\n=== Starting project $proj_name ==="

run_gen_field_const $bitwidth $curve_type $root_dir

open_or_create_solution $sol_name
puts "  -> Solution: $sol_name (bitwidth=$bitwidth, q_type=$q_type)"

# Compiler flags
set q_val [expr {$q_type eq "fixedq" ? "FIXED_Q" : "VAR_Q"}]

set flags ""
append flags " -DBITWIDTH=$bitwidth"
append flags " -DQ_TYPE=$q_val"
append flags " -DCURVE_TYPE=$curve_type"
append flags " -DQ_HEX=\\\"[get_field_const $curve_type q $root_dir]\\\""
append flags " -DQ_PRIME_HEX=\\\"[get_field_const $curve_type q_prime $root_dir]\\\""
append flags " -DMU_HEX=\\\"[get_field_const $curve_type mu $root_dir]\\\""


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

run_osci_test $kernel_dir $work_dir $root_dir $bitwidth \
                $NUM_TEST_SAMPLES $TEST $GEN_SAMPLES $curve_type
if {$TEST_ONLY} { exit }

set_tech_lib $tech_type $root_dir
go libraries

set_clock $period
go assembly

directive set -PIPELINE_INIT_INTERVAL $target_ii
directive set -DESIGN_GOAL latency
go schedule

if {$CCORE_TOP} { branch_if_ccore_comb $kernel }

go extract

run_scverify $kernel_dir $work_dir $bitwidth $SIM
run_syn $tech_type $SYN $root_dir
solution table export -file [file join $work_dir $table_name]
project save