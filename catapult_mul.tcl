# Sweep script for bw group (mul_f, sq_f)

set lvl_dir "lvl0_primitives"
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

# Sweep parameters
set bitwidths {521} ;# 8 12 16 24 32 48 64 96 128 192 256 384 512 768 1024
set tech_types {asic} ;# asic fpga asicgf12
set target_iis {1} ;# 1 2 4 8
set mul_types {kar} ;# kar sb 
set target_periods {3} ;# in ns

set base_mul_depth_map {
    48 {48}
    64 {64}
    96 {48}
    128 {64}
    192 {48}
    254 {63}
    255 {63}
    256 {64}
    381 {47}
    384 {48}
    377 {47}
    448 {56}
    512 {64}
    521 {65}
    768 {48}
    1024 {64}
}

set kar_mul_depth_map {
    8 {8}
    12 {12}
    16 {16}
    24 {24}
    32 {32 16}
    48 {48 24}
    64 {64 32 16}
    96 {96 48 24}
    128 {128 64 32 16}
    192 {192 96 48 24}
    256 {256 128 64 32}
    384 {384 192 96}
    512 {512 256 128}
    521 {521 260 130 65}
    768 {768 384 192 96 48 23}
    1024 {1024 512 256 128 64 32 16}
}

# Control flags
set SIM false ;# verify RTL
set SYN false
set TEST true ;# test C++ code
set TEST_ONLY true ;# only test C++ code with osci, for quick initial testing
set NUM_TEST_SAMPLES 1000
set GEN_SAMPLES true ;# set off if custom samples
set CCORE_TOP false ;# gives us better area/latency for combination units

assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"
override_default_options ;# Reset tool options

foreach tech_type $tech_types {
    set include_dirs {
        utils/include
        lvl0_primitives/mul_f/include
        lvl0_primitives/sq_f/include
    }

    lappend include_dirs [file join $lvl_dir $kernel include]
    set include_flags [build_include_flags $root_dir $include_dirs]

foreach mul_type $mul_types {
foreach period $target_periods {
foreach target_ii $target_iis {
foreach bitwidth $bitwidths {   
    set period_str [string map {. _} $period]
    set proj_name "Catapult_${bitwidth}_${tech_type}_ii${target_ii}_${mul_type}_p${period_str}ns"
    open_or_create_proj $proj_name $work_dir
    puts "\n=== Starting project $proj_name ==="

    set base_mul_depths [dict get $base_mul_depth_map $bitwidth]

foreach bm $base_mul_depths {
    set kar_depths [handle_kar_depths $mul_type $bitwidth $kar_mul_depth_map]

foreach kar $kar_depths {
    set sol_name "sol_bm${bm}_kar${kar}"
    set table_name "table_bw${bitwidth}_tt${tech_type}_ii${target_ii}_mt${mul_type}_p${period}ns.csv"
    set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

    open_or_create_solution $sol_name
    puts "  -> Solution: $sol_name (bitwidth=$bitwidth, bm=$bm, kar=$kar)"

    # Compiler flags
    set mul_val [expr {
        $mul_type eq "kar" ? "MUL_KARATSUBA" :
        ($mul_type eq "sb" ? "MUL_SCHOOLBOOK" : "MUL_NORMAL")
    }]

    set flags ""
    append flags " -DBITWIDTH=$bitwidth"
    append flags " -DMUL_TYPE=$mul_val"
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
    if {$TEST_ONLY} {
        continue
    }

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
    
    if {$CCORE_TOP} {
        branch_if_ccore_comb $kernel 
    }

    go extract
    solution table export -file [file join $work_dir $table_name]
    run_scverify $kernel_dir $work_dir $bitwidth $SIM
    run_syn $tech_type $SYN
    solution table export -file [file join $work_dir $table_name]
}}}
    project save
}}}}
