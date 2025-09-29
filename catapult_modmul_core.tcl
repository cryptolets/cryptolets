# Sweep script for bw group (modmul_mont)
set lvl_dir "lvl1_modops"

# import project level sweep params from env
set tech_type $env(TECH_TYPE)
set period $env(TARGET_PERIOD)
set target_ii $env(TARGET_II)
set mul_type $env(MUL_TYPE)
set bitwidth $env(BITWIDTH)
set q_type $env(Q_TYPE)
set curve_type $env(CURVE_TYPE)
set rtl_file $env(RTL_FILE)
set bm $env(BASE_MUL_DEPTH)
set kar $env(KAR_MUL_DEPTH)

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
}

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
    
set period_str [string map {. _} $period]
set sweep_key "bw${bitwidth}_tt${tech_type}_ii${target_ii}_qt${q_type}_mt${mul_type}_bm${bm}_kar${kar}_p${period_str}ns_ct${curve_type}"
set proj_name "Catapult_${sweep_key}"
set table_name "table_$sweep_key.csv"
set sol_name "sol"
set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

open_or_create_proj $proj_name $work_dir
puts "\n=== Starting project $proj_name ==="

set tmp_const_h_dir [run_const_gens $bitwidth $curve_type $root_dir]
lappend include_dirs [file join $tmp_const_h_dir]
lappend include_dirs [file join $lvl_dir $kernel include]
set include_flags [build_include_flags $root_dir $include_dirs]

set sol_name_test_only "${sol_name}_test_only"

open_or_create_solution $sol_name_test_only
puts "  -> Solution: $sol_name_test_only (bitwidth=$bitwidth, bm=$bm, kar=$kar)"

# Compiler flags
set flags_common ""
append flags " -DBITWIDTH=$bitwidth"
append flags " -DQ_TYPE=[get_q_val $q_type]"
append flags " -DMUL_TYPE=[get_mul_val $mul_type]"
append flags " -DKAR_BASE_MUL_WIDTH=$kar"
append flags " -DBASE_MUL_WIDTH=$bm"
append flags " -DCURVE_TYPE=$curve_type"
options set /Input/CompilerFlags "$include_flags $flags"

# we want only verilog output
options set Output/OutputVHDL false

# rtl schematics take up a ton of space
options set Output/RTLSchem false

# Add kernel + dependencies
solution file add $kernel_dir/src/${kernel}.cpp
solution file add $kernel_dir/src/${kernel}_tb.cpp -exclude true
solution file add [file join $root_dir utils/src/csvparser.cpp] -exclude true
solution file add [file join $root_dir lvl0_primitives/mul_f/src/mul_f.cpp]
solution file add [file join $root_dir lvl0_primitives/sq_f/src/sq_f.cpp]

go analyze
solution design set $kernel -top

go compile
run_osci_test $kernel_dir $work_dir $root_dir $bitwidth \
                $NUM_TEST_SAMPLES $TEST $GEN_SAMPLES $curve_type

if {$TEST_ONLY} { exit }

directive set -OPT_CONST_MULTS full
directive set -PIPELINE_INIT_INTERVAL $target_ii
directive set -DESIGN_GOAL latency
directive set -CCORE_TYPE sequential
directive set -OUTPUT_REGISTERS false
set_tech_lib $tech_type $root_dir


if {$CCORE_MUL_F} {
    # I think it should be safe to use diff clock periods, 
    # since this is what ccore points does
    set mul_period [expr $period * 0.95]

    proc mul_op_run { mul_op bm kar mul_period tech_type} {
        set mul_op_sol_name "${mul_op}"
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
            project save

            return "[solution get /name].[solution get /VERSION]"
        } else {
            set l [project get /SOLUTION/$mul_op_sol_name.v*/VERSION -match glob]
            return "${mul_op_sol_name}.[lindex $l [expr [llength $l] - 1]]"
        }
    }

    if {$mul_type ne "nor"} {
        set mul_f_sol [mul_op_run mul_f $bm $kar $mul_period $tech_type]
        solution table export -file [file join $work_dir $table_name]

        # set sq_f_sol [mul_op_run sq_f $bm $kar $mul_period $tech_type]
        # solution table export -file [file join $work_dir $table_name]
    }
}

# modmul_mont
set modmul_mont_sol_name $sol_name
go new

set_clock $period
solution design set $kernel -top
if {$CCORE_TOP} { solution design set  $kernel -ccore }
if {$CCORE_MUL_F && $mul_type ne "nor"} { solution design set mul_f -ccore }
solution rename $modmul_mont_sol_name
go analyze

if {$CCORE_MUL_F && $mul_type ne "nor"} { solution library add "\[CCORE\] $mul_f_sol" }
go libraries

if {$CCORE_MUL_F && $mul_type ne "nor"} { directive set /$kernel/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol" }
go architect

remove_broken_mul_libs $tech_type

go extract
project save
solution table export -file [file join $work_dir $table_name]

run_scverify $kernel_dir $work_dir $bitwidth $SIM
run_syn $tech_type $SYN $root_dir
solution table export -file [file join $work_dir $table_name]

# solution remove -solution "${sol_name_test_only}.v1" -delete
# project save

project save
# solution remove -solution solution.v1 -delete
# project save
