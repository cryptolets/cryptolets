# Sweep script for point_add
set LVL_DIR "lvl2"
set ROOT_DIR [file normalize [file join [file dirname [info script]] ..]]
source [file join $ROOT_DIR utils util.tcl] ;# Import utilities

# parameter names
set config_params {
    MODMUL_TYPE CURVE_TYPE FIELD_A CURVE_PARAMS_TYPE 
    REDC_TYPE Q_TYPE PREC_TYPE TECH_TYPE TARGET_PERIOD 
    CCORE_PERIOD_RATIO MUL_TYPE CMUL_TYPE TARGET_II BITWIDTH WBW MASK_BITS
    BASE_MUL_WIDTH KAR_BASE_MUL_WIDTH
}
assign_from_env $config_params

# control flags
set SIM $env(SIM)
set SYN $env(SYN)
set TEST $env(TEST)
set TEST_ONLY $env(TEST_ONLY)
set NUM_TEST_SAMPLES $env(NUM_TEST_SAMPLES)
set CCORE_MUL_F $env(CCORE_MUL_F)
set CCORE_MODADDSUB $env(CCORE_MODADDSUB)
set CCORE_MODMUL $env(CCORE_MODMUL)
set CCORE_CMUL $env(CCORE_CMUL)
set CCORE_TOP $env(CCORE_TOP)
set PROCESS_LVL_HANDSHAKE $env(PROCESS_LVL_HANDSHAKE)
set USE_CLUSTERS $env(USE_CLUSTERS)
set CLOCK_UNCERTAINTY_PERCENT 0

# run config
set THREADS_PER_PROCESS $env(THREADS_PER_PROCESS)
set KERNEL_NAME $env(KERNEL_NAME)
set RTL_FILE $env(RTL_FILE)

set SWEEP_KEY $env(SWEEP_KEY)

set KERNEL_DIR [file join $ROOT_DIR $LVL_DIR $KERNEL_NAME]
set WORK_DIR [enter_work_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

set TEST [expr {$SIM || $TEST}]
set HAS_MODSQ [expr {$KERNEL_NAME eq "point_add"}] ;# only for sw, te has no modsq's

# which designs have which const modmuls
set HAS_CMODMUL_A [expr {
    $CURVE_PARAMS_TYPE eq "FIXED_CURVE_PARAMS" && 
    (($KERNEL_NAME eq "point_add" && $FIELD_A eq "AVAR") ||
     ($KERNEL_NAME eq "point_add_te" && $FIELD_A eq "AVAR"))
}]
set HAS_CMODMUL_D [expr {
    $CURVE_PARAMS_TYPE eq "FIXED_CURVE_PARAMS" &&
    ($KERNEL_NAME eq "point_add_te" && $FIELD_A eq "AVAR")
}]
set HAS_CMODMUL_K [expr {
    $CURVE_PARAMS_TYPE eq "FIXED_CURVE_PARAMS" &&
    ($KERNEL_NAME eq "point_add_te" && $FIELD_A eq "ANEG1")
}]

set HAS_CMUL_Q [expr {$CCORE_CMUL && ($Q_TYPE eq "FIXED_Q")}]
set HAS_CMUL_Q_PRIME [expr {
    $CCORE_CMUL && ($MODMUL_TYPE eq "MODMUL_TYPE_MONT") && 
    ($REDC_TYPE eq "FIXED_RC")
}]
set HAS_CMUL_MU [expr {
    ($CCORE_CMUL && $MODMUL_TYPE eq "MODMUL_TYPE_BARRETT") && 
    ($REDC_TYPE eq "FIXED_RC")
}]

if {$MODMUL_TYPE eq "MODMUL_TYPE_BARRETT"} {
    set modmul_suffix "barrett"
    set cmul_suffix ""
} else {
    set modmul_suffix "mont"
    set cmul_suffix "_mont"
}

override_default_options ;# Reset tool options

set proj_name "Catapult_${SWEEP_KEY}"
set table_name "table_${SWEEP_KEY}.csv"
set sol_name $KERNEL_NAME

del_existing_table $table_name

open_or_create_proj $proj_name
puts "\n=== Starting project $proj_name ==="

set json_file [gen_field_consts $FIELD_A]
set tmp_params_h_dir [gen_tmp_params_h $config_params $json_file $CURVE_TYPE]

solution rename "test_only_$sol_name"
puts "  -> Opening solution: $sol_name"

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
    lvl0_primitives/cmul_f/include
    lvl1_modops/modadd/include
    lvl1_modops/modsub/include
    lvl1_modops/include
    lvl1_modops/modmul_mont/include
    lvl1_modops/modmul_barrett/include
}

lappend include_dirs [file join $LVL_DIR $KERNEL_NAME include]
lappend include_dirs [file join $tmp_params_h_dir]
if {$KERNEL_NAME eq "point_add"} {
    lappend include_dirs [file join $ROOT_DIR lvl2/point_double/include]
}
set include_flags [build_include_flags $include_dirs]
options set /Input/CompilerFlags "$include_flags"

# Add kernel + dependencies
solution file add $KERNEL_DIR/src/${KERNEL_NAME}.cpp
solution file add $KERNEL_DIR/src/${KERNEL_NAME}_tb.cpp -exclude true
solution file add [file join $ROOT_DIR utils/src/csvparser.cpp] -exclude true
solution file add [file join $ROOT_DIR lvl0_primitives/mul_f/src/mul_f.cpp]
solution file add [file join $ROOT_DIR lvl0_primitives/sq_f/src/sq_f.cpp]
solution file add [file join $ROOT_DIR lvl0_primitives/cmul_f/src/cmul_f.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modadd/src/modadd.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modsub/src/modsub.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modmul_mont/src/modmul_mont.cpp]
solution file add [file join $ROOT_DIR lvl1_modops/modmul_barrett/src/modmul_barrett.cpp]

if {$KERNEL_NAME eq "point_add"} {
    solution file add [file join $ROOT_DIR lvl2/point_double/src/point_double.cpp]
}

go analyze
solution design set $KERNEL_NAME -top

# Note: FPGA tech node doesn't support this
if {$USE_CLUSTERS && ![is_fpga $TECH_TYPE]} {
    directive set -CLUSTER addtree
    directive set -CLUSTER_FAST_MODE true
}

go compile
run_osci_test $CURVE_TYPE $MODMUL_TYPE
if {$TEST_ONLY} { exit 0 }

directive set -OPT_CONST_MULTS full

if {$PREC_TYPE eq "SINGLE_PREC"} {
    directive set -PIPELINE_INIT_INTERVAL $TARGET_II
}
directive set -DESIGN_GOAL latency
directive set -CCORE_TYPE sequential

if {$CMUL_TYPE ne "CMUL_NORMAL"} {
    directive set REGISTER_THRESHOLD [expr (8 * $BITWIDTH)]
}

if {[is_fpga $TECH_TYPE]} {
    directive set DSP_EXTRACTION yes
    directive set DSP_EXTRACTION_TRAV_PREADD_FANOUT true
    directive set DSP_EXTRACTION_UNFOLD_MAC true
} else {
    directive set -OUTPUT_REGISTERS false
}

set_tech_lib $TECH_TYPE ;# set libraries

proc cmul_op_run { cmul_op cmul_period} {
    global BITWIDTH CLOCK_UNCERTAINTY_PERCENT

    if {[catch {project get /SOLUTION/$cmul_op.v* -match glob} err]} {
        go new
        set_clock $cmul_period $CLOCK_UNCERTAINTY_PERCENT
        solution design set $cmul_op -top -ccore
        solution rename "comb_check_${cmul_op}"
        go compile
        # directive set /$cmul_op -CLUSTER addtree
        go schedule
        branch_if_ccore_comb $cmul_op 

        go new
        solution rename $cmul_op

        go extract
        project save

        return "[solution get /name].[solution get /VERSION]"
    } else {
        set l [project get /SOLUTION/$cmul_op.v*/VERSION -match glob]
        return "${cmul_op}.[lindex $l [expr [llength $l] - 1]]"
    }
}

if {$CCORE_CMUL} {
    set cmul_period [expr $TARGET_PERIOD * $CCORE_PERIOD_RATIO * 0.75] ;# custom tuning for edge cases

    if {$HAS_CMUL_Q} {
        set cmul_q_sol [cmul_op_run cmul_q $cmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    if {$HAS_CMUL_Q_PRIME} {
        set cmul_q_prime_sol [cmul_op_run cmul_q_prime $cmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    if {$HAS_CMUL_MU} {
        set cmul_mu_sol [cmul_op_run cmul_mu $cmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    if {$HAS_CMODMUL_A} {
        set cmul_field_a_sol [cmul_op_run "cmul_field_a${cmul_suffix}" $cmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    if {$HAS_CMODMUL_D} {
        set cmul_field_d_sol [cmul_op_run "cmul_field_d${cmul_suffix}" $cmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    if {$HAS_CMODMUL_K} {
        set cmul_field_k_sol [cmul_op_run "cmul_field_k${cmul_suffix}" $cmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }
}

# I think it should be safe to use diff clock periods, 
# since this is what ccore_points does
set mod_ops_period [expr $TARGET_PERIOD * $CCORE_PERIOD_RATIO]

if {$CCORE_MUL_F} {
    # I think it should be safe to use diff clock periods, 
    # since this is what ccore points does
    set mul_period [expr $mod_ops_period * $CCORE_PERIOD_RATIO]

    proc mul_op_run { mul_op mul_period} {
        global TECH_TYPE CLOCK_UNCERTAINTY_PERCENT

        if {[catch {project get /SOLUTION/$mul_op.v* -match glob} err]} {
            go new
            set_clock $mul_period $CLOCK_UNCERTAINTY_PERCENT
            solution design set $mul_op -top -ccore
            solution rename "comb_check_${mul_op}"
            go architect
            remove_broken_mul_libs $TECH_TYPE
            go schedule

            branch_if_ccore_comb $mul_op 

            go new
            solution rename $mul_op

            go extract
            project save
            return "[solution get /name].[solution get /VERSION]"
        } else {
            set l [project get /SOLUTION/$mul_op.v*/VERSION -match glob]
            return "${mul_op}.[lindex $l [expr [llength $l] - 1]]"
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

if {$CCORE_MODMUL} {
    proc modmul_run {modmul_name mod_ops_period} {
        if {[catch {project get /SOLUTION/$modmul_name.v* -match glob} err]} {
            global TECH_TYPE MUL_TYPE CCORE_MUL_F CCORE_CMUL sq_f_sol mul_f_sol \
                HAS_CMUL_Q HAS_CMUL_Q_PRIME HAS_CMUL_MU cmul_suffix modmul_suffix \
                cmul_q_sol cmul_q_prime_sol cmul_mu_sol \
                cmul_field_a_sol cmul_field_d_sol cmul_field_k_sol \
                CLOCK_UNCERTAINTY_PERCENT

            go new
            set_clock $mod_ops_period $CLOCK_UNCERTAINTY_PERCENT
            solution design set ${modmul_name}_core -top -ccore
            if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
                if {$modmul_name eq "modsq_${modmul_suffix}"} {
                    solution design set sq_f -ccore
                }
                solution design set mul_f -ccore
            }
            if {$HAS_CMUL_Q} { solution design set "cmul_q" -ccore }
            if {$HAS_CMUL_Q_PRIME} { solution design set "cmul_q_prime" -ccore }
            if {$HAS_CMUL_MU} { solution design set "cmul_mu" -ccore }
            if {$CCORE_CMUL} {
                if {$modmul_name eq "cmodmul_a_${modmul_suffix}"} { solution design set "cmul_field_a${cmul_suffix}" -ccore }
                if {$modmul_name eq "cmodmul_d_${modmul_suffix}"} { solution design set "cmul_field_d${cmul_suffix}" -ccore }
                if {$modmul_name eq "cmodmul_k_${modmul_suffix}"} { solution design set "cmul_field_k${cmul_suffix}" -ccore }
            }

            solution rename "comb_check_$modmul_name"

            go analyze
            if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
                if {$modmul_name eq "modsq_${modmul_suffix}"} {
                    solution library add "\[CCORE\] $sq_f_sol"
                } else {
                    solution library add "\[CCORE\] $mul_f_sol"
                }
            }
            if {$HAS_CMUL_Q} { solution library add "\[CCORE\] $cmul_q_sol" }
            if {$HAS_CMUL_Q_PRIME} { solution library add "\[CCORE\] $cmul_q_prime_sol" }
            if {$HAS_CMUL_MU} { solution library add "\[CCORE\] $cmul_mu_sol" }
            if {$CCORE_CMUL} {
                if {$modmul_name eq "cmodmul_a_${modmul_suffix}"} { solution library add "\[CCORE\] $cmul_field_a_sol" }
                if {$modmul_name eq "cmodmul_d_${modmul_suffix}"} { solution library add "\[CCORE\] $cmul_field_d_sol" }
                if {$modmul_name eq "cmodmul_k_${modmul_suffix}"} { solution library add "\[CCORE\] $cmul_field_k_sol" }
            }

            go compile

            go libraries
            if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
                if {$modmul_name eq "modsq_${modmul_suffix}"} {
                    directive set /${modmul_name}_core/sq_f -MAP_TO_MODULE "\[CCORE\] $sq_f_sol"
                }
                directive set /${modmul_name}_core/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol"
            }
            if {$HAS_CMUL_Q} { directive set /${modmul_name}_core/cmul_q -MAP_TO_MODULE "\[CCORE\] $cmul_q_sol" }
            if {$HAS_CMUL_Q_PRIME} { directive set /${modmul_name}_core/cmul_q_prime -MAP_TO_MODULE "\[CCORE\] $cmul_q_prime_sol" }
            if {$HAS_CMUL_MU} { directive set /${modmul_name}_core/cmul_mu -MAP_TO_MODULE "\[CCORE\] $cmul_mu_sol" }
            if {$CCORE_CMUL} {
                if {$modmul_name eq "cmodmul_a_${modmul_suffix}"} { directive set "/${modmul_name}_core/cmul_field_a${cmul_suffix}" -MAP_TO_MODULE "\[CCORE\] $cmul_field_a_sol" }
                if {$modmul_name eq "cmodmul_d_${modmul_suffix}"} { directive set "/${modmul_name}_core/cmul_field_d${cmul_suffix}" -MAP_TO_MODULE "\[CCORE\] $cmul_field_d_sol" }
                if {$modmul_name eq "cmodmul_k_${modmul_suffix}"} { directive set "/${modmul_name}_core/cmul_field_k${cmul_suffix}" -MAP_TO_MODULE "\[CCORE\] $cmul_field_k_sol" }
            }

            go architect
            remove_broken_mul_libs $TECH_TYPE
            go schedule

            branch_if_ccore_comb "${modmul_name}_core"

            go new
            solution rename $modmul_name

            go extract
            project save
            return "[solution get /name].[solution get /VERSION]"
        } else {
            # get latest version name
            set l [project get /SOLUTION/$modmul_name.v*/VERSION -match glob]
            return "${modmul_name}.[lindex $l [expr [llength $l] - 1]]"
        }
    }

    set modmul_sol [modmul_run "modmul_${modmul_suffix}" $mod_ops_period]
    solution table export -file [file join $WORK_DIR $table_name]

    if {$HAS_MODSQ} {
        set modsq_sol [modmul_run "modsq_${modmul_suffix}" $mod_ops_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    set cmodmul_period $mod_ops_period
    if {$HAS_CMODMUL_A} {
        set cmodmul_a_sol [modmul_run "cmodmul_a_${modmul_suffix}" $cmodmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    if {$HAS_CMODMUL_D} {
        set cmodmul_d_sol [modmul_run "cmodmul_d_${modmul_suffix}" $cmodmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }

    if {$HAS_CMODMUL_K} {
        set cmodmul_k_sol [modmul_run "cmodmul_k_${modmul_suffix}" $cmodmul_period]
        solution table export -file [file join $WORK_DIR $table_name]
    }
}

if {$CCORE_MODADDSUB} {
    proc mod_ops_run { mod_op mod_ops_period } {
        global CLOCK_UNCERTAINTY_PERCENT

        if {[catch {project get /SOLUTION/$mod_op.v* -match glob} err]} {
            go new
            set_clock $mod_ops_period $CLOCK_UNCERTAINTY_PERCENT
            solution design set "${mod_op}_core" -top -ccore
            solution rename "comb_check_${mod_op}"
            go schedule
            branch_if_ccore_comb "${mod_op}_core"

            go new
            solution rename $mod_op

            go extract
            project save
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
set_clock $TARGET_PERIOD $CLOCK_UNCERTAINTY_PERCENT
solution design set $KERNEL_NAME -top
if {$CCORE_MODMUL} {
    solution design set "modmul_${modmul_suffix}_core" -ccore
    if {$HAS_MODSQ} {
        solution design set "modsq_${modmul_suffix}_core" -ccore
    }
    if {$HAS_CMODMUL_A} {
        solution design set "cmodmul_a_${modmul_suffix}_core" -ccore
    }
    if {$HAS_CMODMUL_D} {
        solution design set "cmodmul_d_${modmul_suffix}_core" -ccore
    }
    if {$HAS_CMODMUL_K} {
        solution design set "cmodmul_k_${modmul_suffix}_core" -ccore
    }
}
if {$CCORE_MODADDSUB} {
    solution design set modadd_core -ccore
    solution design set modsub_core -ccore
    solution design set moddouble_core -ccore
}
solution rename "test_only_${sol_name}"

go analyze
if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
    solution library add "\[CCORE\] $mul_f_sol" 
}
if {$HAS_MODSQ} {
    if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
        solution library add "\[CCORE\] $sq_f_sol"
    }
    if {$CCORE_MODMUL} {
        solution library add "\[CCORE\] $modsq_sol"
    }
}
if {$CCORE_MODMUL} {
    solution library add "\[CCORE\] $modmul_sol"
    if {$HAS_CMODMUL_A} {
        solution library add "\[CCORE\] $cmodmul_a_sol"
    }
    if {$HAS_CMODMUL_D} {
        solution library add "\[CCORE\] $cmodmul_d_sol"
    }
    if {$HAS_CMODMUL_K} {
        solution library add "\[CCORE\] $cmodmul_k_sol"
    }
}
if {$CCORE_MODADDSUB} {
    solution library add "\[CCORE\] $modadd_sol"
    solution library add "\[CCORE\] $modsub_sol"
    solution library add "\[CCORE\] $moddouble_sol"
}
if {$HAS_CMUL_Q} { solution library add "\[CCORE\] $cmul_q_sol" }
if {$HAS_CMUL_Q_PRIME} { solution library add "\[CCORE\] $cmul_q_prime_sol" }
if {$HAS_CMUL_MU} { solution library add "\[CCORE\] $cmul_mu_sol" }
if {$CCORE_CMUL} {
    if {$HAS_CMODMUL_A} { solution library add "\[CCORE\] $cmul_field_a_sol" }
    if {$HAS_CMODMUL_D} { solution library add "\[CCORE\] $cmul_field_d_sol" }
    if {$HAS_CMODMUL_K} { solution library add "\[CCORE\] $cmul_field_k_sol" }
}

go libraries
if {$CCORE_MODMUL} {
    directive set "/$KERNEL_NAME/modmul_${modmul_suffix}_core" -MAP_TO_MODULE "\[CCORE\] $modmul_sol"
    if {$HAS_MODSQ} { directive set "/$KERNEL_NAME/modsq_${modmul_suffix}_core" -MAP_TO_MODULE "\[CCORE\] $modsq_sol" }
    if {$HAS_CMODMUL_A} { directive set "/$KERNEL_NAME/cmodmul_a_${modmul_suffix}_core" -MAP_TO_MODULE "\[CCORE\] $cmodmul_a_sol" }
    if {$HAS_CMODMUL_D} { directive set "/$KERNEL_NAME/cmodmul_d_${modmul_suffix}_core" -MAP_TO_MODULE "\[CCORE\] $cmodmul_d_sol" }
    if {$HAS_CMODMUL_K} { directive set "/$KERNEL_NAME/cmodmul_k_${modmul_suffix}_core" -MAP_TO_MODULE "\[CCORE\] $cmodmul_k_sol" }
}
if {$CCORE_MODADDSUB} {
    directive set /$KERNEL_NAME/modadd_core -MAP_TO_MODULE "\[CCORE\] $modadd_sol"
    directive set /$KERNEL_NAME/modsub_core -MAP_TO_MODULE "\[CCORE\] $modsub_sol"
    directive set /$KERNEL_NAME/moddouble_core -MAP_TO_MODULE "\[CCORE\] $moddouble_sol"
}

extract_verify_syn_save
exit 0