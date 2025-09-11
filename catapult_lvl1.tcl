# Sweep script for bw group (modadd, modsub)

set lvl_dir "lvl1_modops"
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

# Sweep parameters
set bitwidths {128}
set tech_types {asic} ;# asic fpga asicgf12
set target_iis {1}
set target_periods {3} ;# in ns
set q_types {varq} ;# varq fixedq

# Control flags
set SIM false ;# verify RTL
set SYN false
set TEST false ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set CCORE_TOP true ;# gives us better area/latency for combination units

assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"
override_default_options ;# Reset tool options

foreach tech_type $tech_types {
foreach q_type $q_types {
    set include_dirs {
        utils/include
    }

    lappend include_dirs [file join $lvl_dir $kernel include]
    set include_flags [build_include_flags $root_dir $include_dirs]

foreach period $target_periods {
foreach target_ii $target_iis {
foreach bitwidth $bitwidths {
    set period_str [string map {. _} $period]
    set proj_name "Catapult_${bitwidth}_${tech_type}_ii${target_ii}_${q_type}_p${period_str}ns"
    set table_name "table_bw${bitwidth}_tt${tech_type}_ii${target_ii}_qt${q_type}_p${period}ns.csv"
    set sol_name "sol_qt${q_type}"
    set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

    open_or_create_proj $proj_name $work_dir
    puts "\n=== Starting project $proj_name ==="

    open_or_create_solution $sol_name
    puts "  -> Solution: $sol_name (bitwidth=$bitwidth, q_type=$q_type)"

    # Compiler flags
    set q_val [expr {$q_type eq "fixedq" ? "FIXED_Q" : "VAR_Q"}]

    set flags ""
    append flags " -DBITWIDTH=$bitwidth"
    append flags " -DQ_TYPE=$q_val"

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

    run_osci_test $kernel_dir $work_dir $bitwidth $NUM_TEST_SAMPLES $TEST $GEN_SAMPLES
    if {$TEST_ONLY} {
        continue
    }

    set_tech_lib $tech_type $root_dir
    go libraries

    set_clock $period
    go assembly

    directive set -PIPELINE_INIT_INTERVAL $target_ii
    directive set -DESIGN_GOAL latency
    go schedule

    if {$CCORE_TOP} {
        branch_if_ccore_comb $kernel 
    }
    
    go extract

    run_scverify $kernel_dir $work_dir $bitwidth $SIM
    run_syn $tech_type $SYN
    solution table export -file [file join $work_dir $table_name]
    project save
}}}}}
