# Sweep script for bw group (modmul_mont)

set lvl_dir "lvl1_modops"
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

# Sweep parameters
set bitwidths {256} ;# 64 128 256 384
set tech_types {asic} ;# fpga asic asicgf12
set target_iis {1}
set mul_types {sb} ;# mul_types: kar sb nor
set target_periods {3} ;# in ns
set base_mul_depths_pow2 {64} ;# 128 64 32 16
set base_mul_depths_nonpow2 {48} ;# 192 96 48 24
set q_types {varq} ;#varq fixedq

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
    768 {768 384 192 96 48 23}
    1024 {1024 512 256 128 64 32 16}
}

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
        lvl0_primitives/mul_f/include
        lvl0_primitives/sq_f/include
    }
    
    if {$q_type eq "fixedq"} {
        lappend include_dirs "lvl0_primitives/cmul_f/include"
    }

    lappend include_dirs [file join $lvl_dir $kernel include]
    set include_flags [build_include_flags $root_dir $include_dirs]
    
foreach mul_type $mul_types {
foreach period $target_periods {
foreach target_ii $target_iis {
foreach bitwidth $bitwidths {
	set proj_name "Catapult_${bitwidth}_${tech_type}_ii${target_ii}_${mul_type}_p${period}ns"
    open_or_create_proj $proj_name $work_dir
    puts "\n=== Starting project $proj_name ==="

    # different base_mul_depths for pow2 bitwidths and bitwidths like, 96,192,384,etc.
    set base_mul_depths [handle_base_mul_depths $mul_type $bitwidth $base_mul_depths_pow2 $base_mul_depths_nonpow2]

foreach bm $base_mul_depths {
    set kar_depths [handle_kar_depths $mul_type $bitwidth $kar_mul_depth_map]

foreach kar $kar_depths {
    set sol_name "sol_bm${bm}_kar${kar}_qt${q_type}"
    set table_name "table_bw${bitwidth}_tt${tech_type}_ii${target_ii}_mt${mul_type}_p${period}ns.csv"
    set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

    open_or_create_solution $sol_name
    puts "  -> Solution: $sol_name (bitwidth=$bitwidth, bm=$bm, kar=$kar, q_type=$q_type)"

    # Compiler flags
    set q_val [expr {$q_type eq "fixedq" ? "FIXED_Q" : "VAR_Q"}]
    set mul_val [expr {
        $mul_type eq "kar" ? "MUL_KARATSUBA" :
        ($mul_type eq "sb" ? "MUL_SCHOOLBOOK" : "MUL_NORMAL")
    }]

    set flags ""
    append flags " -DBITWIDTH=$bitwidth"
    append flags " -DQ_TYPE=$q_val"
    append flags " -DMUL_TYPE=$mul_val"
    append flags " -DKAR_BASE_MUL_WIDTH=$kar"
    append flags " -DBASE_MUL_WIDTH=$bm"

    options set /Input/CompilerFlags "$include_flags $flags"

    # Add kernel + dependencies
    solution file add $kernel_dir/src/${kernel}.cpp
    solution file add $kernel_dir/src/${kernel}_tb.cpp -exclude true
    solution file add [file join $root_dir utils/src/csvparser.cpp] -exclude true
    solution file add [file join $root_dir lvl0_primitives/cmul_f/src/cmul_f.cpp]
    solution file add [file join $root_dir lvl0_primitives/mul_f/src/mul_f.cpp]
    solution file add [file join $root_dir lvl0_primitives/sq_f/src/sq_f.cpp]
    if {$q_type eq "varq"} {
        solution file remove [file join $root_dir lvl0_primitives/cmul_f/src/cmul_f.cpp]
    }

    go analyze
    solution design set $kernel -top

    go compile
    run_osci_test $kernel_dir $work_dir $bitwidth $NUM_TEST_SAMPLES $TEST $GEN_SAMPLES
    if {$TEST_ONLY} {
        continue
    }

    directive set -OPT_CONST_MULTS full
    directive set -PIPELINE_INIT_INTERVAL $target_ii
    directive set -DESIGN_GOAL latency
    directive set -CCORE_TYPE sequential
    directive set -OUTPUT_REGISTERS false
    set_tech_lib $tech_type $root_dir

    # I think it should be safe to use diff clock periods, 
    # since this is what ccore points does
    set mul_period [expr $period * 0.95]

    proc mul_op_run { mul_op bm kar mul_period tech_type} {
        set mul_op_sol_name "${mul_op}_bm${bm}_kar${kar}"
        if {[catch {project get /SOLUTION/$mul_op_sol_name.v* -match glob} err]} {
            go new
            set_clock $mul_period
            solution design set $mul_op -top -ccore
            solution rename $mul_op_sol_name
            go architect
            remove_broken_mul_libs $tech_type
            go schedule

            branch_if_ccore_comb $mul_op 
            go extract

            return "[solution get /name].[solution get /VERSION]"
        } else {
            set l [project get /SOLUTION/$mul_op_sol_name.v*/VERSION -match glob]
            return "${mul_op_sol_name}.[lindex $l [expr [llength $l] - 1]]"
        }
    }

    set mul_f_sol [mul_op_run mul_f $bm $kar $mul_period $tech_type]
    solution table export -file [file join $work_dir $table_name]

    # set sq_f_sol [mul_op_run sq_f $bm $kar $mul_period $tech_type]
    # solution table export -file [file join $work_dir $table_name]

    # cmul_f
    if {$q_type eq "fixedq"} {
        set cmul_sol_name "cmul_f"
        if {[catch {project get /SOLUTION/$cmul_sol_name.v* -match glob} err]} {
            go new
            set_clock $mul_period
            solution design set cmul_f -top -ccore
            solution rename $cmul_sol_name
            go extract
            set cmul_f_sol "[solution get /name].[solution get /VERSION]"
            solution table export -file [file join $work_dir $table_name]
        } else {
            set l [project get /SOLUTION/$cmul_sol_name.v*/VERSION -match glob]
            set cmul_f_sol "${cmul_sol_name}.[lindex $l [expr [llength $l] - 1]]"
        }
    }

    # modmul_mont
    set modmul_mont_sol_name $sol_name
    go new

    set_clock $period_ns
    solution design set modmul_mont_core -top
    if {$CCORE_TOP} {
        solution design set modmul_mont_core -ccore
    }
    solution design set mul_f -ccore
    if {$q_type eq "fixedq"} {
        solution design set cmul_f -ccore
    }
    solution rename $modmul_mont_sol_name
    go analyze

    solution library add "\[CCORE\] $mul_f_sol"
    if {$q_type eq "fixedq"} {
        solution library add "\[CCORE\] $cmul_f_sol"
    }
    go libraries
    
    directive set /modmul_mont_core/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol"
    if {$q_type eq "fixedq"} {
        directive set /modmul_mont_core/cmul_f -MAP_TO_MODULE "\[CCORE\] $cmul_f_sol"
    }

    go extract
    solution table export -file [file join $work_dir $table_name]
    run_scverify $kernel_dir $work_dir $bitwidth $SIM
    run_syn $tech_type $SYN
    solution table export -file [file join $work_dir $table_name]
}}}
	project save

}}}}}
