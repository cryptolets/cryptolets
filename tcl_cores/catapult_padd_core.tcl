# Sweep script for point_add
set LVL_DIR "lvl2"
set ROOT_DIR [file normalize [file join [file dirname [info script]] ..]]
source [file join $ROOT_DIR utils util.tcl] ;# Import utilities

# parameter names
set config_params {
    CURVE_TYPE FIELD_A Q_TYPE PREC_TYPE TECH_TYPE TARGET_PERIOD 
    CCORE_PERIOD_RATIO MUL_TYPE TARGET_II BITWIDTH WBW MASK_BITS
    BASE_MUL_WIDTH KAR_BASE_MUL_WIDTH
}
assign_from_env $config_params

# control flags
set SIM $env(SIM)
set SYN $env(SYN)
set TEST $env(TEST)
set TEST_ONLY $env(TEST_ONLY)
set NUM_TEST_SAMPLES $env(NUM_TEST_SAMPLES)
set GEN_SAMPLES $env(GEN_SAMPLES)
set CCORE_MUL_F $env(CCORE_MUL_F)
set CCORE_MODADDSUB $env(CCORE_MODADDSUB)
set HAS_MODSQ $env(HAS_MODSQ)

# run config
set THREADS_PER_PROCESS $env(THREADS_PER_PROCESS)
set KERNEL_NAME $env(KERNEL_NAME)
set RTL_FILE $env(RTL_FILE)

set SWEEP_KEY $env(SWEEP_KEY)

set KERNEL_DIR [file join $ROOT_DIR $LVL_DIR $KERNEL_NAME]
set WORK_DIR [enter_work_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

set TEST [expr {$SIM || $TEST}]

override_default_options ;# Reset tool options

set proj_name "Catapult_${SWEEP_KEY}"
set table_name "table_${SWEEP_KEY}.csv"
set sol_name $KERNEL_NAME
set sol_name_test_only "${sol_name}_test_only"

open_or_create_proj $proj_name
puts "\n=== Starting project $proj_name ==="

set json_file [gen_field_consts $FIELD_A]
set tmp_params_h_dir [gen_tmp_params_h $config_params $json_file $CURVE_TYPE]

open_or_create_solution $sol_name_test_only
puts "  -> Opening solution: $sol_name_test_only"

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
    lvl1_modops/modadd/include
    lvl1_modops/modsub/include
    lvl1_modops/modmul_mont/include
    lvl1_modops/include
}

lappend include_dirs [file join $LVL_DIR $KERNEL_NAME include]
lappend include_dirs [file join $tmp_params_h_dir]
set include_flags [build_include_flags $include_dirs]
options set /Input/CompilerFlags "$include_flags"

# Add kernel + dependencies
solution file add $KERNEL_DIR/src/${KERNEL_NAME}.cpp
solution file add $KERNEL_DIR/src/${KERNEL_NAME}_tb.cpp -exclude true
solution file add [file join $ROOT_DIR utils/src/csvparser.cpp] -exclude true
solution file add [file join $ROOT_DIR lvl0_primitives/mul_f/src/mul_f.cpp]
solution file add [file join $ROOT_DIR lvl0_primitives/sq_f/src/sq_f.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modadd/src/modadd.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modsub/src/modsub.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modmul_mont/src/modmul_mont.cpp]

go analyze
solution design set $KERNEL_NAME -top

go compile
run_osci_test $CURVE_TYPE
if {$TEST_ONLY} { exit }

directive set -OPT_CONST_MULTS full
if {$PREC_TYPE eq "SINGLE_PREC"} {
    directive set -PIPELINE_INIT_INTERVAL $TARGET_II
}
directive set -DESIGN_GOAL latency
directive set -CCORE_TYPE sequential
directive set -OUTPUT_REGISTERS false
set_tech_lib $TECH_TYPE ;# set libraries

# I think it should be safe to use diff clock periods, 
# since this is what ccore_points does
set mod_ops_period [expr $TARGET_PERIOD * $CCORE_PERIOD_RATIO]

if {$CCORE_MUL_F} {
    # I think it should be safe to use diff clock periods, 
    # since this is what ccore points does
    set mul_period [expr $mod_ops_period * $CCORE_PERIOD_RATIO]

    proc mul_op_run { mul_op mul_period} {
        glob TECH_TYPE

        set mul_op_sol_name "${mul_op}"
        if {[catch {project get /SOLUTION/$mul_op_sol_name.v* -match glob} err]} {
            go new
            set_clock $mul_period
            solution design set $mul_op -top -ccore
            solution rename $mul_op_sol_name
            go architect
            remove_broken_mul_libs $TECH_TYPE
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

    if {$MUL_TYPE ne "MUL_NORMAL"} {
        set mul_f_sol [mul_op_run mul_f $mul_period]
        solution table export -file [file join $WORK_DIR $table_name]

        if {$HAS_MODSQ} {
            set sq_f_sol [mul_op_run sq_f $bm $kar $mul_period $tech_type]
            solution table export -file [file join $work_dir $table_name]
        }
    }
}

proc modmul_run {modmul_name mod_ops_period} {
    if {[catch {project get /SOLUTION/$modmul_name.v* -match glob} err]} {
        global TECH_TYPE MUL_TYPE CCORE_MUL_F sq_f_sol mul_f_sol

        go new
        set_clock $mod_ops_period
        solution design set ${modmul_name}_core -top -ccore
        if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
            if {$modmul_name eq "modsq_mont"} {
                solution design set sq_f -ccore
            }
            solution design set mul_f -ccore
        }
        solution rename $modmul_name

        go analyze
        if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
            if {$modmul_name eq "modsq_mont"} {
                solution library add "\[CCORE\] $sq_f_sol"
            } else {
                solution library add "\[CCORE\] $mul_f_sol"
            }
        }

        go libraries
        if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
            if {$modmul_name eq "modsq_mont"} {
                directive set /${modmul_name}_core/sq_f -MAP_TO_MODULE "\[CCORE\] $sq_f_sol"
            }
            directive set /${modmul_name}_core/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol"
        }

        go architect
        remove_broken_mul_libs $TECH_TYPE

        go extract
        return "[solution get /name].[solution get /VERSION]"
    } else {
        # get latest version name
        set l [project get /SOLUTION/$modmul_name.v*/VERSION -match glob]
        return "${modmul_name}.[lindex $l [expr [llength $l] - 1]]"
    }
}

set modmul_sol [modmul_run modmul_mont $mod_ops_period]
solution table export -file [file join $WORK_DIR $table_name]

if {$HAS_MODSQ} {
    set modsq_sol [modmul_run modsq_mont $mod_ops_period]
    solution table export -file [file join $WORK_DIR $table_name]
}

if {$CCORE_MODADDSUB} {
    proc mod_ops_run { mod_op mod_ops_period } {
        if {[catch {project get /SOLUTION/$mod_op.v* -match glob} err]} {
            go new
            set_clock $mod_ops_period
            solution design set "${mod_op}_core" -top -ccore -combinational
            solution rename $mod_op
            go extract
            return "[solution get /name].[solution get /VERSION]"
        } else {
            # get latest version name
            set l [project get /SOLUTION/$mod_op.v*/VERSION -match glob]
            return "${mod_op}.[lindex $l [expr [llength $l] - 1]]"
        }
    }

    set modadd_sol [mod_ops_run modadd $mod_ops_period]
    solution table export -file [file join $WORK_DIR $table_name]
    set modsub_sol [mod_ops_run modsub $mod_ops_period]
    solution table export -file [file join $WORK_DIR $table_name]
    set moddouble_sol [mod_ops_run moddouble $mod_ops_period]
    solution table export -file [file join $WORK_DIR $table_name]
}

go new
set_clock $TARGET_PERIOD
solution design set $KERNEL_NAME -top
solution design set modmul_mont_core -ccore
if {$HAS_MODSQ} {
    solution design set modsq_mont_core -ccore
}
if {$CCORE_MODADDSUB} {
    solution design set modadd_core -ccore
    solution design set modsub_core -ccore
    solution design set moddouble_core -ccore
}
solution rename $sol_name

go analyze
if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} { 
    solution library add "\[CCORE\] $mul_f_sol" 
}
if {$HAS_MODSQ} {
    if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
        solution library add "\[CCORE\] $sq_f_sol"
    }
    solution library add "\[CCORE\] $modsq_sol"
}
solution library add "\[CCORE\] $modmul_sol"
if {$CCORE_MODADDSUB} {
    solution library add "\[CCORE\] $modadd_sol"
    solution library add "\[CCORE\] $modsub_sol"
    solution library add "\[CCORE\] $moddouble_sol"
}


go libraries
directive set /$KERNEL_NAME/modmul_mont_core -MAP_TO_MODULE "\[CCORE\] $modmul_sol"
if {$HAS_MODSQ} { directive set /$KERNEL_NAME/modsq_mont_core -MAP_TO_MODULE "\[CCORE\] $modsq_sol" }
if {$CCORE_MODADDSUB} {
    directive set /$KERNEL_NAME/modadd_core -MAP_TO_MODULE "\[CCORE\] $modadd_sol"
    directive set /$KERNEL_NAME/modsub_core -MAP_TO_MODULE "\[CCORE\] $modsub_sol"
    directive set /$KERNEL_NAME/moddouble_core -MAP_TO_MODULE "\[CCORE\] $moddouble_sol"
}

go extract
project save
solution table export -file [file join $WORK_DIR $table_name]
run_scverify
run_syn $TECH_TYPE

solution table export -file [file join $WORK_DIR $table_name]
project save