# Sweep script for bw group (modmul_mont)
set lvl_dir "lvl2"

# import project level sweep params from env
set tech_type $env(TECH_TYPE)
set period $env(TARGET_PERIOD)
set target_ii $env(TARGET_II)
set mul_type $env(MUL_TYPE)
set bitwidth $env(BITWIDTH)
set q_type $env(Q_TYPE)
set curve_type $env(CURVE_TYPE)
set bm $env(BASE_MUL_DEPTH)
set kar $env(KAR_MUL_DEPTH)

set kernel $env(KERNEL_NAME)
set root_dir [file normalize [file dirname [info script]]]
source [file join $root_dir catapult_padd_params.tcl] ;# get solution level params and control flags

# Import utilities
source [file join $root_dir utils util.tcl]

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

override_default_options ;# Reset tool options

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
    lvl1_modops/modadd/include
    lvl1_modops/modsub/include
    lvl1_modops/modmul_mont/include
}

lappend include_dirs [file join $lvl_dir $kernel include]
set include_flags [build_include_flags $root_dir $include_dirs]
    
set period_str [string map {. _} $period]
set sweep_key "bw${bitwidth}_tt${tech_type}_ii${target_ii}_qt${q_type}_mt${mul_type}_bm${bm}_kar${kar}_p${period_str}ns_ct${curve_type}"
set proj_name "Catapult_${sweep_key}"
set table_name "table_$sweep_key.csv"
set sol_name "sol"

open_or_create_proj $proj_name $work_dir
puts "\n=== Starting project $proj_name ==="

run_gen_field_const $bitwidth $curve_type $root_dir

set sol_name_test_only "${sol_name}_test_only"
open_or_create_solution $sol_name_test_only
puts "  -> Solution: $sol_name_test_only (bitwidth=$bitwidth, bm=$bm, kar=$kar, q_type=$q_type)"

# Compiler flags
set flags ""
append flags " -DBITWIDTH=$bitwidth"
append flags " -DQ_TYPE=[get_q_val $q_type]"
append flags " -DMUL_TYPE=[get_mul_val $mul_type]"
append flags " -DKAR_BASE_MUL_WIDTH=$kar"
append flags " -DBASE_MUL_WIDTH=$bm"
append flags " -DCURVE_TYPE=$curve_type"
append flags " -DQ_HEX=\\\"[get_field_const $curve_type q $root_dir]\\\""
append flags " -DQ_PRIME_HEX=\\\"[get_field_const $curve_type q_prime $root_dir]\\\""
append flags " -DMU_HEX=\\\"[get_field_const $curve_type mu $root_dir]\\\""

options set /Input/CompilerFlags "$include_flags $flags"

# Add kernel + dependencies
solution file add $kernel_dir/src/${kernel}.cpp
solution file add $kernel_dir/src/${kernel}_tb.cpp -exclude true
solution file add [file join $root_dir utils/src/csvparser.cpp] -exclude true
solution file add [file join $root_dir lvl0_primitives/mul_f/src/mul_f.cpp]
solution file add [file join $root_dir lvl0_primitives/sq_f/src/sq_f.cpp]
solution file add [file join $root_dir lvl1_modops/modadd/src/modadd.cpp]
solution file add [file join $root_dir lvl1_modops/modsub/src/modsub.cpp]
solution file add [file join $root_dir lvl1_modops/modmul_mont/src/modmul_mont.cpp]

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

# I think it should be safe to use diff clock periods, since this is 
# what ccore_points does, 
set mod_ops_period [expr $period * 0.95]

if {$CCORE_MUL_F} {
    set mul_period [expr $mod_ops_period * 0.95]

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

            return "[solution get /name].[solution get /VERSION]"
        } else {
            set l [project get /SOLUTION/$mul_op_sol_name.v*/VERSION -match glob]
            return "${mul_op_sol_name}.[lindex $l [expr [llength $l] - 1]]"
        }
    }

    if {$mul_type ne "nor"} {
        set mul_f_sol [mul_op_run mul_f $bm $kar $mul_period $tech_type]
        solution table export -file [file join $work_dir $table_name]

        if {$HAS_MODSQ} {
            set sq_f_sol [mul_op_run sq_f $bm $kar $mul_period $tech_type]
            solution table export -file [file join $work_dir $table_name]
        }
    }
}

# modmul_mont
set modmul_mont_sol_name "modmul_mont"
if {[catch {project get /SOLUTION/$modmul_mont_sol_name.v* -match glob} err]} {
    go new
    set_clock $mod_ops_period
    solution design set modmul_mont_core -top -ccore
    if {$CCORE_MUL_F && $mul_type ne "nor"} { solution design set mul_f -ccore }
    solution rename $modmul_mont_sol_name

    go analyze
    if {$CCORE_MUL_F && $mul_type ne "nor"} { solution library add "\[CCORE\] $mul_f_sol" }

    go libraries
    if {$CCORE_MUL_F && $mul_type ne "nor"} { directive set /modmul_mont_core/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol"}

    go extract
    solution table export -file [file join $work_dir $table_name]
    set modmul_mont_sol "[solution get /name].[solution get /VERSION]"
} else {
    # get latest version name
    set l [project get /SOLUTION/$modmul_mont_sol_name.v*/VERSION -match glob]
    set modmul_mont_sol "${modmul_mont_sol_name}.[lindex $l [expr [llength $l] - 1]]"
}

# modsq_mont
if {$HAS_MODSQ} {
    set modsq_mont_sol_name "modsq_mont"
    if {[catch {project get /SOLUTION/$modsq_mont_sol_name.v* -match glob} err]} {
        go new
        set_clock $mod_ops_period
        solution design set modsq_mont_core -top -ccore
        if {$CCORE_MUL_F && $mul_type ne "nor"} { solution design set sq_f -ccore }
        solution rename $modsq_mont_sol_name

        go analyze
        if {$CCORE_MUL_F && $mul_type ne "nor"} {
            solution library add "\[CCORE\] $sq_f_sol"
            solution library add "\[CCORE\] $mul_f_sol"
        }

        go libraries
        if {$CCORE_MUL_F && $mul_type ne "nor"} {
            directive set /modsq_mont_core/sq_f -MAP_TO_MODULE "\[CCORE\] $sq_f_sol"
            directive set /modsq_mont_core/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol"
        }
        go extract
        solution table export -file [file join $work_dir $table_name]
        set modsq_mont_sol "[solution get /name].[solution get /VERSION]"
    } else {
        # get latest version name
        set l [project get /SOLUTION/$modsq_mont_sol_name.v*/VERSION -match glob]
        set modsq_mont_sol "${modsq_mont_sol_name}.[lindex $l [expr [llength $l] - 1]]"
    }
}

if {$CCORE_MODADDSUB} {
    proc mod_ops_run { mod_op q_type mod_ops_period } {
        set modop_sol_name "${mod_op}_qt${q_type}"
        if {[catch {project get /SOLUTION/$modop_sol_name.v* -match glob} err]} {
            go new
            set_clock $mod_ops_period
            solution design set "${mod_op}_core" -top -ccore -combinational
            solution rename $modop_sol_name
            go extract
            return "[solution get /name].[solution get /VERSION]"
        } else {
            # get latest version name
            set l [project get /SOLUTION/$modop_sol_name.v*/VERSION -match glob]
            return "${modop_sol_name}.[lindex $l [expr [llength $l] - 1]]"
        }
    }

    set modadd_sol [mod_ops_run modadd $q_type $mod_ops_period]
    solution table export -file [file join $work_dir $table_name]
    set modsub_sol [mod_ops_run modsub $q_type $mod_ops_period]
    solution table export -file [file join $work_dir $table_name]
    set moddouble_sol [mod_ops_run moddouble $q_type $mod_ops_period]
    solution table export -file [file join $work_dir $table_name]
}

# padd
go new
set_clock $period
solution design set $kernel -top
solution design set modmul_mont_core -ccore
if {$HAS_MODSQ} { solution design set modsq_mont_core -ccore }
if {$CCORE_MODADDSUB} {
    solution design set modadd_core -ccore
    solution design set modsub_core -ccore
    solution design set moddouble_core -ccore
}
solution rename $sol_name

go analyze
if {$CCORE_MUL_F && $mul_type ne "nor"} { 
    solution library add "\[CCORE\] $mul_f_sol" 
}
if {$HAS_MODSQ} {
    if {$CCORE_MUL_F && $mul_type ne "nor"} {
        solution library add "\[CCORE\] $sq_f_sol"
    }
    solution library add "\[CCORE\] $modsq_mont_sol"
}
solution library add "\[CCORE\] $modmul_mont_sol"
if {$CCORE_MODADDSUB} {
    solution library add "\[CCORE\] $modadd_sol"
    solution library add "\[CCORE\] $modsub_sol"
    solution library add "\[CCORE\] $moddouble_sol"
}

go libraries
directive set /$kernel/modmul_mont_core -MAP_TO_MODULE "\[CCORE\] $modmul_mont_sol"
if {$HAS_MODSQ} { directive set /$kernel/modsq_mont_core -MAP_TO_MODULE "\[CCORE\] $modsq_mont_sol" }
if {$CCORE_MODADDSUB} {
    directive set /$kernel/modadd_core -MAP_TO_MODULE "\[CCORE\] $modadd_sol"
    directive set /$kernel/modsub_core -MAP_TO_MODULE "\[CCORE\] $modsub_sol"
    directive set /$kernel/moddouble_core -MAP_TO_MODULE "\[CCORE\] $moddouble_sol"
}

go extract
solution table export -file [file join $work_dir $table_name]
run_scverify $kernel_dir $work_dir $bitwidth $SIM
run_syn $tech_type $SYN $root_dir
solution table export -file [file join $work_dir $table_name]

project save
