# catapult_lvl0.tcl
# Sweep script for bw group (add_f, sub_f, cmul_f)

set lvl_dir "lvl0_primitives"
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

# Sweep parameters
set bitwidths {32}
set tech_types {asic} ;# asic fpga asicgf12
set target_iis {1}
set target_freqs {300}

# Control flags
set SIM true ;# verify RTL
set SYN false
set TEST true ;# test C++ code
set TEST_ONLY false ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set CCORE_TOP false

assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"
override_default_options ;# Reset tool options

foreach tech_type $tech_types {
    set include_dirs {
        utils/include
    }
    lappend include_dirs [file join $lvl_dir $kernel include]
    set include_flags [build_include_flags $root_dir $include_dirs]

foreach freq $target_freqs {
foreach target_ii $target_iis {
foreach bitwidth $bitwidths {
    set proj_name "Catapult_${bitwidth}_${tech_type}_ii${target_ii}_${freq}MHz"
    open_or_create_proj $proj_name $work_dir
    puts "\n=== Starting project $proj_name ==="

    set sol_name "sol"
    set table_name "table_bw${bitwidth}_tt${tech_type}_ii${target_ii}_f${freq}MHz.csv"
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
    }
    go compile

    run_osci_test $kernel_dir $work_dir $bitwidth $NUM_TEST_SAMPLES $TEST $GEN_SAMPLES
    if {$TEST_ONLY} {
        continue
    }

    set_tech_lib $tech_type $root_dir ;# set libraries
    go libraries

    set period_ns [expr {(1000.0 / $freq) * 1}]
    set_clock $period_ns
    go assembly

    directive set -PIPELINE_INIT_INTERVAL $target_ii
    directive set -DESIGN_GOAL latency

    go extract
    solution table export -file [file join $work_dir $table_name]
    run_scverify $kernel_dir $work_dir $bitwidth $SIM
    run_syn $tech_type $SYN
    solution table export -file [file join $work_dir $table_name]
    project save
}}}}
