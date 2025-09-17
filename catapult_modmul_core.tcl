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

set kernel $env(KERNEL_NAME)
set root_dir [file normalize [file dirname [info script]]]

# Import utilities
source [file join $root_dir utils util.tcl]
source [file join $root_dir catapult_modmul_params.tcl] ;# get solution level params and control flags

set kernel_dir [file join $root_dir $lvl_dir $kernel]
set work_dir [enter_work_dir $kernel_dir] ;# move to a lvl_dir/kernel/Catapult as working dir

assert {!(($CCORE_TOP && $TEST) || $CCORE_TOP && $SIM)} "top cannot be ccore for sim or test"
override_default_options ;# Reset tool options

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
    
set period_str [string map {. _} $period]
set sweep_key "bw${bitwidth}_tt${tech_type}_ii${target_ii}_qt${q_type}_mt${mul_type}_p${period_str}ns_ct${curve_type}"
set proj_name "Catapult_${sweep_key}"

open_or_create_proj $proj_name $work_dir
puts "\n=== Starting project $proj_name ==="

run_gen_field_const $bitwidth $curve_type $root_dir

set base_mul_depths [dict get $base_mul_depth_map $bitwidth]
set kar_depths [handle_kar_depths $mul_type $bitwidth $kar_mul_depth_map]

foreach bm $base_mul_depths {
    foreach kar $kar_depths {
        set sol_name "sol_bm${bm}_kar${kar}"
        set table_name "table_$sweep_key.csv"
        set CCORE_TOP [expr {$CCORE_TOP && $target_ii <= 1}]

        open_or_create_solution $sol_name
        puts "  -> Solution: $sol_name (bitwidth=$bitwidth, bm=$bm, kar=$kar)"

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
        solution file add [file join $root_dir lvl0_primitives/cmul_f/src/cmul_f.cpp]
        solution file add [file join $root_dir lvl0_primitives/mul_f/src/mul_f.cpp]
        solution file add [file join $root_dir lvl0_primitives/sq_f/src/sq_f.cpp]
        if {$q_type eq "varq"} {
            solution file remove [file join $root_dir lvl0_primitives/cmul_f/src/cmul_f.cpp]
        }

        go analyze
        solution design set $kernel -top

        go compile
        run_osci_test $kernel_dir $work_dir $root_dir $bitwidth \
                        $NUM_TEST_SAMPLES $TEST $GEN_SAMPLES $curve_type
        if {$TEST_ONLY} { continue }

        directive set -OPT_CONST_MULTS full
        directive set -PIPELINE_INIT_INTERVAL $target_ii
        directive set -DESIGN_GOAL latency
        directive set -CCORE_TYPE sequential
        directive set -OUTPUT_REGISTERS false
        set_tech_lib $tech_type $root_dir

        # I think it should be safe to use diff clock periods, 
        # since this is what ccore points does
        set mul_period [expr $period * 1]

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

        if {$mul_type ne "nor"} {
            set mul_f_sol [mul_op_run mul_f $bm $kar $mul_period $tech_type]
            solution table export -file [file join $work_dir $table_name]

            # set sq_f_sol [mul_op_run sq_f $bm $kar $mul_period $tech_type]
            # solution table export -file [file join $work_dir $table_name]
        }

        # cmul_f
        if {$q_type eq "fixedq"} {
            set cmul_sol_name "cmul_f"
            if {[catch {project get /SOLUTION/$cmul_sol_name.v* -match glob} err]} {
                go new
                set_clock $mul_period
                solution design set cmul_f -top -ccore
                solution rename $cmul_sol_name
                go schedule
                branch_if_ccore_comb $cmul_sol_name 
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

        set_clock $period
        solution design set modmul_mont_core -top
        if {$CCORE_TOP} { solution design set modmul_mont_core -ccore }
        if {$mul_type ne "nor"} { solution design set mul_f -ccore }
        if {$q_type eq "fixedq"} { solution design set cmul_f -ccore }
        solution rename $modmul_mont_sol_name
        go analyze

        if {$mul_type ne "nor"} { solution library add "\[CCORE\] $mul_f_sol" }
        if {$q_type eq "fixedq"} { solution library add "\[CCORE\] $cmul_f_sol" }
        go libraries
        
        if {$mul_type ne "nor"} { directive set /modmul_mont_core/mul_f -MAP_TO_MODULE "\[CCORE\] $mul_f_sol" }
        if {$q_type eq "fixedq"} { directive set /modmul_mont_core/cmul_f -MAP_TO_MODULE "\[CCORE\] $cmul_f_sol" }
        go architect

        remove_broken_mul_libs $tech_type

        go extract
        solution table export -file [file join $work_dir $table_name]
        run_scverify $kernel_dir $work_dir $bitwidth $SIM
        run_syn $tech_type $SYN $root_dir
        solution table export -file [file join $work_dir $table_name]
    }
}

project save
