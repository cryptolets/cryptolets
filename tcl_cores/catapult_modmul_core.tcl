# Sweep script for bw group (modmul_mont, modmul_barrett)
set LVL_DIR "lvl1_modops"
set ROOT_DIR [file normalize [file join [file dirname [info script]] ..]]
source [file join $ROOT_DIR utils util.tcl] ;# Import utilities

# parameter names
set config_params {
    MUL_SQ CURVE_TYPE REDC_TYPE Q_TYPE PREC_TYPE TECH_TYPE TARGET_PERIOD 
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
set CCORE_TOP $env(CCORE_TOP)
set CCORE_MUL_F $env(CCORE_MUL_F)
set CCORE_CMUL $env(CCORE_CMUL)
set USE_CLUSTERS $env(USE_CLUSTERS)

# run config
set THREADS_PER_PROCESS $env(THREADS_PER_PROCESS)
set KERNEL_NAME $env(KERNEL_NAME)
set RTL_FILE $env(RTL_FILE)

set SWEEP_KEY $env(SWEEP_KEY)

set KERNEL_DIR [file join $ROOT_DIR $LVL_DIR $KERNEL_NAME]
set WORK_DIR [enter_work_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

assert {!($CCORE_TOP && $PREC_TYPE eq "MULTI_PREC")} "top cannot be ccore for multi-precision"

set TEST [expr {$SIM || $TEST}]
set CCORE_TOP [expr {$CCORE_TOP && $TARGET_II <= 1}]
set HAS_CMUL_Q [expr {$CCORE_CMUL && ($Q_TYPE eq "FIXED_Q")}]
set HAS_CMUL_Q_PRIME [expr {$CCORE_CMUL && ($KERNEL_NAME eq "modmul_mont") && ($REDC_TYPE eq "FIXED_RC")}]
set HAS_CMUL_MU [expr {($CCORE_CMUL && $KERNEL_NAME eq "modmul_barrett") && ($REDC_TYPE eq "FIXED_RC")}]

override_default_options ;# Reset tool options

set proj_name "Catapult_${SWEEP_KEY}"
set table_name "table_${SWEEP_KEY}.csv"
set sol_name $KERNEL_NAME

open_or_create_proj $proj_name
puts "\n=== Starting project $proj_name ==="

del_existing_table $table_name

set json_file [gen_field_consts]
set tmp_params_h_dir [gen_tmp_params_h $config_params $json_file $CURVE_TYPE]

solution rename "test_only_$sol_name"
puts "  -> Opening solution: $sol_name"

set include_dirs {
    utils/include
    lvl0_primitives/mul_f/include
    lvl0_primitives/sq_f/include
    lvl0_primitives/cmul_f/include
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
solution file add [file join $ROOT_DIR lvl0_primitives/cmul_f/src/cmul_f.cpp]

go analyze
solution design set $KERNEL_NAME -top

if {$USE_CLUSTERS && ![is_fpga $TECH_TYPE]} {
    directive set -CLUSTER addtree
    directive set -CLUSTER_FAST_MODE true
}

go compile
run_osci_test $CURVE_TYPE
if {$TEST_ONLY} { exit 0 }

if {$PREC_TYPE eq "SINGLE_PREC"} {
    directive set -PIPELINE_INIT_INTERVAL $TARGET_II
}
directive set -DESIGN_GOAL latency
directive set -CCORE_TYPE sequential
directive set -OUTPUT_REGISTERS false
directive set -OPT_CONST_MULTS full

if {$CMUL_TYPE ne "CMUL_NORMAL"} {
    directive set REGISTER_THRESHOLD [expr (8 * $BITWIDTH)]
}
if {[is_fpga $TECH_TYPE]} {
    directive set DSP_EXTRACTION yes
    directive set DSP_EXTRACTION_TRAV_PREADD_FANOUT true
    directive set DSP_EXTRACTION_UNFOLD_MAC true
}
set_tech_lib $TECH_TYPE ;# set libraries

proc cmul_op_run { cmul_op cmul_period} {    
    global BITWIDTH

    if {[catch {project get /SOLUTION/$cmul_op.v* -match glob} err]} {
        go new
        set_clock $cmul_period
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
    set cmul_period [expr $TARGET_PERIOD * $CCORE_PERIOD_RATIO]

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
}

if {$CCORE_MUL_F} {
    # I think it should be safe to use diff clock periods, 
    # since this is what ccore points does
    set mul_period [expr $TARGET_PERIOD * $CCORE_PERIOD_RATIO]

    proc mul_op_run { mul_op mul_period} {
        global TECH_TYPE

        if {[catch {project get /SOLUTION/$mul_op.v* -match glob} err]} {
            go new
            set_clock $mul_period
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
        if {$MUL_SQ == 0} {
            set mul_f_sol [mul_op_run mul_f $mul_period]
            solution table export -file [file join $WORK_DIR $table_name]
        } else {
            set sq_f_sol [mul_op_run sq_f $mul_period]
            solution table export -file [file join $WORK_DIR $table_name]
        }
    }
}


go new
set_clock $TARGET_PERIOD
solution design set $KERNEL_NAME -top

if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
    if {$MUL_SQ == 0} { solution design set mul_f -ccore }
    else { solution design set sq_f -ccore }
}
if {$HAS_CMUL_Q} { solution design set "cmul_q" -ccore }
if {$HAS_CMUL_Q_PRIME} { solution design set "cmul_q_prime" -ccore }
if {$HAS_CMUL_MU} { solution design set "cmul_mu" -ccore }

solution rename "test_only_$sol_name"
go compile

if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} {
    if {$MUL_SQ == 0} { solution library add "\[CCORE\] $mul_f_sol" }
    else { solution library add "\[CCORE\] $sq_f_sol" }
}
if {$HAS_CMUL_Q} { solution library add "\[CCORE\] $cmul_q_sol" }
if {$HAS_CMUL_Q_PRIME} {solution library add "\[CCORE\] $cmul_q_prime_sol" }
if {$HAS_CMUL_MU} { solution library add "\[CCORE\] $cmul_mu_sol" }
go libraries

if {$CCORE_MUL_F && $MUL_TYPE ne "MUL_NORMAL"} { 
    if {$MUL_SQ == 0} {
        directive set /$KERNEL_NAME/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol" 
    } else {
        directive set /$KERNEL_NAME/sq_f -MAP_TO_MODULE "\[CCORE\] $sq_f_sol"
    }
}
if {$HAS_CMUL_Q} { directive set /$KERNEL_NAME/cmul_q -MAP_TO_MODULE "\[CCORE\] $cmul_q_sol" }
if {$HAS_CMUL_Q_PRIME} { directive set /$KERNEL_NAME/cmul_q_prime -MAP_TO_MODULE "\[CCORE\] $cmul_q_prime_sol" }
if {$HAS_CMUL_MU} { directive set /$KERNEL_NAME/cmul_mu -MAP_TO_MODULE "\[CCORE\] $cmul_mu_sol" }
go architect

remove_broken_mul_libs $TECH_TYPE
go schedule

extract_verify_syn_save
exit 0