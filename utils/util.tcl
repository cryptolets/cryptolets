# utils/util.tcl
# Common helper procs for Catapult

# Ensure kernel/Catapult dir exists and cd into it
proc enter_work_dir {} {
    global KERNEL_DIR

    set work_dir [file join $KERNEL_DIR Catapult]
    if {![file exists $work_dir]} {
        file mkdir $work_dir
    }
    cd $work_dir
    return $work_dir
}

proc assign_from_env {params} {
    foreach p $params {
        if {[info exists ::env($p)]} {
            set ::$p $::env($p)
        } else {
            puts "Warning: env($p) not defined"
        }
    }
}

proc override_default_options {} {
    options defaults
    options set /Input/CppStandard c++14
    options set /Input/TargetPlatform x86_64
    options set Output/OutputVHDL false ;# we want only verilog output
    options set Output/RTLSchem false ;# rtl schematics take up a ton of space
    options set Flows/SCVerify/MAX_ERROR_CNT 1
    options set Flows/DesignCompiler/OutNetlistFormat verilog
    options set Flows/Vivado/XILINX_VIVADO /eda/xilinx//Vivado/2024.2/
}

proc is_fpga {tech_type} {
    # all fpga tech types start with "fpga"
    return [string match "fpga*" $tech_type]
}

proc set_tech_lib {tech_type} {
    global ROOT_DIR
    
    solution library remove *
    if {$tech_type eq "45nm"} {
        set custom_dc_script_path [file normalize "$ROOT_DIR/dc_custom_scripts"]
        options set Flows/DesignCompiler/CustomScriptDirPath "$custom_dc_script_path"
        options set ComponentLibs/TechLibSearchPath [file normalize "$ROOT_DIR/../45nm_db"] -append

        solution library add nangate-45nm_beh \
            -- -rtlsyntool DesignCompiler -vendor Nangate -technology 045nm
    } elseif {$tech_type eq "gf12"} {
        set custom_dc_script_path [file normalize "$ROOT_DIR/dc_custom_scripts"]
        options set Flows/DesignCompiler/CustomScriptDirPath "$custom_dc_script_path"
        options set ComponentLibs/TechLibSearchPath "/ip/arm/gf12/sc7p5mcpp84_base_slvt_c14/r1p0/db" -append

        solution library add sc7p5mcpp84_12lp_base_slvt_c14_tt_nominal_max_0p90v_25c_dc \
            -file "$ROOT_DIR/../gf12_libs/sc7p5mcpp84_12lp_base_slvt_c14_tt_nominal_max_0p90v_25c_dc_smooth.lib" \
            -- -rtlsyntool DesignCompiler -vendor GlobalFoundries -technology 012nm

    } elseif {$tech_type eq "saed32"} {
        # add custom dc script path
        set custom_dc_script_path [file normalize "$ROOT_DIR/dc_custom_scripts"]
        options set Flows/DesignCompiler/CustomScriptDirPath "$custom_dc_script_path"
        # it prob just needs some of these paths, but linking all for now just to be safe 
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/tech/tf" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/lib/stdcell_lvt/lef" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/lib/stdcell_lvt/db_nldm" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/lib/stdcell_lvt/db_ccs" -append

        solution library add saed32lvt_tt0p78v125c_beh \
            -- -rtlsyntool DesignCompiler -vendor SAED32 -technology {lvt tt0p78v125c}        
    } elseif {$tech_type eq "fpga_hbmvh1782"} {
        # Top of the line Versal HBM
        solution library add mgc_Xilinx-VERSAL-hbm-3HP_beh \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VERSAL-hbm -speed -3HP \
            -part xcvh1782-lsva4737-3HP-e-S
    } elseif {$tech_type eq "fpga_hbmvh1582"} {
        solution library add mgc_Xilinx-VERSAL-hbm-2MP_beh \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VERSAL-hbm -speed -2MP \
            -part xcvh1582-vsva3697-2MP-e-S
    } elseif {$tech_type eq "fpga_vu9p"} {
        # Virtex Ultra+ used by other papers
        solution library add mgc_Xilinx-VIRTEX-uplus-2_beh \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VIRTEX-uplus -speed -2 \
            -part xcvu9p-flga2104-2-i
    } elseif {$tech_type eq "fpga_hbmvh1782_custom"} {
        # "*_custom" denotes a custom library file
        # Top of the line Versal HBM
        solution library add mgc_Xilinx-VERSAL-hbm-3HP_beh \
            -file "$ROOT_DIR/../custom_fpga_catapult_libs/mgc_Xilinx-VERSAL-hbm-3HP_beh.lib" \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VERSAL-hbm -speed -3HP \
            -part xcvh1782-lsva4737-3HP-e-S
    } elseif {$tech_type eq "fpga_hbmvh1582_custom"} {
        # Versal HBM used in evaluation kit
        solution library add mgc_Xilinx-VERSAL-hbm-2MP_beh \
            -file "$ROOT_DIR/../custom_fpga_catapult_libs/mgc_Xilinx-VERSAL-hbm-2MP_beh.lib" \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VERSAL-hbm -speed -2MP \
            -part xcvh1582-vsva3697-2MP-e-S
    } elseif {$tech_type eq "fpga_vu9p_custom"} {
        # Virtex UltraScale+ used by other papers
        solution library add mgc_Xilinx-VIRTEX-uplus-2_beh \
            -file "$ROOT_DIR/../custom_fpga_catapult_libs/mgc_Xilinx-VIRTEX-uplus-2_beh.lib" \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VIRTEX-uplus -speed -2 \
            -part xcvu9p-flga2104-2-i
    }
}

# Project handling
proc open_or_create_proj {proj_name} {
    global WORK_DIR

    set proj_ccs [file join $WORK_DIR "${proj_name}.ccs"]
    set proj_dir [file join $WORK_DIR $proj_name]

    if {[file exists $proj_dir]} {
        puts "Removing existing project dir: $proj_dir"
        file delete -force $proj_dir
    }
    if {[file exists $proj_ccs]} {
        puts "Removing existing project file: $proj_ccs"
        file delete -force $proj_ccs
    }

    puts "Creating new project: $proj_name"
    project new -name $proj_name -directory $proj_dir
    project save
}

proc del_existing_table {table_name} {
    global WORK_DIR
    set table_file [file join $WORK_DIR "${table_name}"]

    if {[file exists $table_file]} {
        puts "Removing existing table file: $table_file"
        file delete -force $table_file
    }
}

# Clock constraints
proc set_clock {period {clock_uncertainty_ratio 0}} {
    set clk_high_time [expr {$period / 2}]
    set clk_uncertainty [expr {$period * $clock_uncertainty_ratio}]

    directive set -CLOCKS [
        list clk [list \
            -CLOCK_PERIOD $period \
            -CLOCK_UNCERTAINTY $clk_uncertainty \
            -CLOCK_HIGH_TIME $clk_high_time \
        ]
    ]
}

# Build include flags from list of include dirs
proc build_include_flags {include_dirs} {
    global ROOT_DIR
    set include_flags ""
    foreach dir $include_dirs {
        append include_flags " -I[file join $ROOT_DIR $dir]"
    }
    return $include_flags
}

proc gen_field_consts {{FIELD_A "A0"}} {
    global BITWIDTH ROOT_DIR CURVE_TYPE

    set proj_dir [project get /PROJECT_DIR]
    set py_exec [file join $ROOT_DIR .venv/bin/ python]

    if {$CURVE_TYPE ne "RAND_CURVE"} {
        puts "\[INFO\] Skipping field constant generation (curve_type=$CURVE_TYPE)"
        return [file join $ROOT_DIR field_const.json]
    }

    set json_file [file join $proj_dir field_const.json]
    set gen_field_const_py [file join $ROOT_DIR utils gen_field_const.py]
    set cmd [list $py_exec $gen_field_const_py --bitwidth $BITWIDTH --json-file $json_file --field-a $FIELD_A]

    exec tcsh -c "$cmd"
    return $json_file
}

proc gen_tmp_params_h {config_params {json_file ""} {CURVE_TYPE ""}} {
    global ROOT_DIR

    set proj_dir [project get /PROJECT_DIR]
    set py_exec [file join $ROOT_DIR .venv/bin/ python]

    set gen_params_h_py [file join $ROOT_DIR utils gen_params_h.py]
    set tmp_params_dir [file join $proj_dir include]
    file mkdir $tmp_params_dir
    set tmp_params_fp [file join $tmp_params_dir tmp_params.h]

    # Build --params argument list from config_params array
    set param_args {}
    foreach key $config_params {
        if {[info exists ::env($key)]} {
            set val $::env($key)
            lappend param_args "${key}=${val}"
        } else {
            puts "\[WARN\] env($key) not defined"
        }
    }

    # Base command
    set cmd [list $py_exec $gen_params_h_py --out $tmp_params_fp]

    # Add optional JSON and curve args
    if {$CURVE_TYPE ne "" && $json_file ne ""} {
        lappend cmd --json-file $json_file --curve-type $CURVE_TYPE
    }

    # Add runtime params
    lappend cmd --params {*}$param_args

    exec tcsh -c "$cmd"
    return $tmp_params_dir
}

proc run_osci_test {{CURVE_TYPE ""} {MODMUL_TYPE ""} {BITSHIFT_DIRECTION ""}} {
    global TEST BITWIDTH KERNEL_DIR ROOT_DIR NUM_TEST_SAMPLES MUL_SQ
    # generate samples csv file and run initial C++ tests
    if {$TEST} {
        set proj_dir [project get /PROJECT_DIR]
        set outputs_dir [file join $proj_dir outputs]
        if {![file isdirectory $outputs_dir]} {
            file mkdir $outputs_dir
        }

        set sample_fp [file join $proj_dir samples/samples_${BITWIDTH}.csv]
        set output_fp [file join $outputs_dir output_${BITWIDTH}.csv]
        set golden_fp [file join $proj_dir goldens/golden_${BITWIDTH}.csv]

        set py_exec [file join $ROOT_DIR .venv/bin/ python]
        set cmd [list $py_exec [file join $KERNEL_DIR gen_samples.py] \
            --bw $BITWIDTH \
            --n $NUM_TEST_SAMPLES \
            --samples-file $sample_fp \
            --golden-file $golden_fp]

        if {$CURVE_TYPE ne ""} {
            if {$CURVE_TYPE ne "RAND_CURVE"} {
                set json_file [file join $ROOT_DIR field_const.json]
            } else {
                set json_file [file join $proj_dir field_const.json]
            }

            lappend cmd --curve_type $CURVE_TYPE
            lappend cmd --json-file $json_file
        }

        if {$MODMUL_TYPE ne ""} {
            lappend cmd --modmul-type $MODMUL_TYPE
        }

        if {$BITSHIFT_DIRECTION ne ""} {
            lappend cmd --bitshift-direction $BITSHIFT_DIRECTION
        }
        
        if {[info exists MUL_SQ] && $MUL_SQ == 1} {
            lappend cmd --mul-sq
        }

        puts "running cmd: $cmd"
        exec tcsh -c "$cmd"

        flow package require /SCVerify
        flow package option set /SCVerify/INVOKE_ARGS "$sample_fp $output_fp"
        flow run /SCVerify/launch_make ./scverify/Verify_orig_cxx_osci.mk {} SIMTOOL=osci sim

        # check if golden and output match
        if {[catch {exec diff -q $golden_fp $output_fp}]} {
            puts "ERROR: Verifying C++ with osci BITWIDTH=$BITWIDTH"
            exit 1
        } else {
            puts "PASS: Output matches golden for BITWIDTH=$BITWIDTH"
        }
    }
}

# This logic is because if we make CCORE_TOP we cannot do verify
proc extract_verify_syn_save {} {
    global WORK_DIR KERNEL_NAME sol_name table_name \
            SIM CCORE_TOP TECH_TYPE PROCESS_LVL_HANDSHAKE
    
    go new ;# doing this otherwise there will be issues in gui
    if {$SIM || $CCORE_TOP} {
        solution rename "test_only_$sol_name"
    } else {
        solution rename $sol_name
    }

    go extract
    project save
    solution table export -file [file join $WORK_DIR $table_name]
    run_scverify

    if {$CCORE_TOP} {
        go libraries
        
        solution rename "comb_check_$sol_name"
        solution design set $KERNEL_NAME -ccore
        
        if {![info exists PROCESS_LVL_HANDSHAKE]} { set PROCESS_LVL_HANDSHAKE false }
        if {$PROCESS_LVL_HANDSHAKE} {
            directive set TRANSACTION_DONE_SIGNAL false
            directive set /$KERNEL_NAME -CCORE_SYNC_MODE handshake   
        }

        go schedule
        branch_if_ccore_comb $KERNEL_NAME
    } 
    
    if {$SIM || $CCORE_TOP} {
        go new
        solution rename $sol_name
    }

    go extract
    project save
    solution table export -file [file join $WORK_DIR $table_name]

    run_syn $TECH_TYPE
    solution table export -file [file join $WORK_DIR $table_name]
    project save
}

proc run_scverify {} {
    global BITWIDTH SIM

    if {$SIM} {
        options set Flows/QuestaSIM/Path /eda/mentor/questasim/linux_x86_64
        # If MGLS_LICENSE_FILE is set, copy it to SALT_LICENSE_SERVER
        if { [info exists ::env(MGLS_LICENSE_FILE)] } {
            set ::env(SALT_LICENSE_SERVER) $::env(MGLS_LICENSE_FILE)
        }

        puts "Sim: Running SCVerify for BITWIDTH=$BITWIDTH"
        set proj_dir [project get /PROJECT_DIR]
        set sample_fp [file join $proj_dir samples/samples_${BITWIDTH}.csv]
        set output_fp [file join $proj_dir outputs/output_${BITWIDTH}.csv]
        set golden_fp [file join $proj_dir goldens/golden_${BITWIDTH}.csv]

        if {[file exists $output_fp]} {
            file delete -force $output_fp
        }

        flow package require /SCVerify
        flow package option set /SCVerify/INVOKE_ARGS "$sample_fp $output_fp"
        flow run /SCVerify/launch_make ./scverify/Verify_rtl_v_msim.mk {} SIMTOOL=msim sim

        if {[catch {exec diff -q $golden_fp $output_fp}]} {
            puts "ERROR: Verifying with SCVerify BITWIDTH=$BITWIDTH"
            exit 1
        } else {
            puts "PASS: Output matches golden for BITWIDTH=$BITWIDTH"
        }
    }
}

proc inject_threads_vivado {syn_file_path} {
    global THREADS_PER_PROCESS

    # Read file
    set fh [open $syn_file_path r]
    set content [read $fh]
    close $fh

    # Block to inject
    set thread_block "# --- injected by Catapult wrapper ---
set_param general.maxThreads $THREADS_PER_PROCESS
set_param synth.maxThreads   $THREADS_PER_PROCESS
puts \"MAX THREADS: general=\[get_param general.maxThreads\] synth=\[get_param synth.maxThreads\]\"
# --- end injection ---"

    # Prepend
    set new_content "$thread_block\n\n$content"

    # Write back
    set fh [open $syn_file_path w]
    puts $fh $new_content
    close $fh
}

proc run_syn {tech_type} {
    global SYN RTL_FILE

    if {$SYN} {
        if {$tech_type eq "fpga" || $tech_type eq "fpgahbm" || $tech_type eq "fpgahbmvhk158"} {
            puts "Syn: Running FPGA Vivado synthesis"

            # Fixes issue with running Vivado for Versal HBM fpga
            set ::env(LD_LIBRARY_PATH) "/eda/xilinx/Vivado/2024.2/lib/lnx64.o"
            catch {unset ::env(LD_PRELOAD)}
            puts "LD_LIBRARY_PATH is now: $::env(LD_LIBRARY_PATH)"

            set syn_file_path [file join [solution get /SOLUTION_DIR] "vivado_v" "rtl.v.xv"]
            inject_threads_vivado $syn_file_path

            if {[catch {flow run /Vivado/synthesize -shell $syn_file_path} err]} {
                puts "ERROR: Vivado synthesis failed -> $err"
                return -code error $err
            }
        } elseif {$tech_type eq "45nm" || $tech_type eq "saed32" || $tech_type eq "gf12"} {
            puts "Syn: Running Design Compiler for $tech_type"
            
            # Replace compile commands with compile_ultra in the DC synthesis file
            # Get the full path to the generated DC file
            set dc_file_path [file join [solution get /SOLUTION_DIR] "${RTL_FILE}.v.dc"]
            if {[file exists $dc_file_path]} {
                replace_compile_with_ultra $dc_file_path
            } else {
                puts "Warning: DC file not found at $dc_file_path"
                return
            }

            # ERROR HANDLING DOESN'T WORK
            if {[catch {flow run /DesignCompiler/dc_shell ./$RTL_FILE.v.dc} err]} {
                puts "ERROR: DC synthesis failed -> $err"
                return -code error $err
            }
        }
    }
}

proc branch_if_ccore_comb {kernel} {
    set latency_cycles [solution get /DATUM/FIELDS/timing/COLUMNS/tm_latency_cycles/VALUE]

    if {$latency_cycles == 0} {
        # for combinational
        go libraries
        solution design set $kernel -combinational
        go architect
    }
}

proc assert {condition {msg "assertion failed"}} {
    if {![uplevel 1 [list expr $condition]]} {
        error $msg
    }
}

proc get_field_const {curve_type const root_dir} {    
    if {$curve_type eq "RAND_CURVE"} {
        set proj_dir [project get /PROJECT_DIR]
        set json_fp [file join $proj_dir field_const.json]
    } else {
        set json_fp [file join $root_dir field_const.json]
    }
    return [exec python3 -c "import json;print(json.load(open('$json_fp'))\['$curve_type'\]\['$const'\])"]
}

proc remove_broken_mul_libs { tech_type } {
    # Make sure mgc_mul's with blank MinClkPrd are not used

    if {[is_fpga $tech_type]} {
        # Don't use mgc_mul or mgc_sqr > 64b, up till 2999b
        for {set i 7} {$i <= 9} {incr i 1} {
            for {set j 0} {$j <= 9} {incr j 1} {
                directive set "/.../*mgc_mul(${i}${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr(${i}${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_mul_pipe(${i}${j},*,2,0,1)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr_pipe(${i}${j},*,2,0,1)" -match glob -QUANTITY 0

                if {$tech_type eq "45nm"} {
                    directive set "/.../*mgc_mul_pipe(${i}${j},*,2,0,2)" -match glob -QUANTITY 0
                    directive set "/.../*mgc_sqr_pipe(${i}${j},*,2,0,2)" -match glob -QUANTITY 0
                }
            }
        }
        
        for {set i 0} {$i <= 9} {incr i 1} {
            for {set j 0} {$j <= 9} {incr j 1} {
                directive set "/.../*mgc_mul(${i}?${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr(${i}?${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_mul_pipe(${i}?${j},*,2,0,1)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr_pipe(${i}?${j},*,2,0,1)" -match glob -QUANTITY 0

                if {$tech_type eq "45nm"} {
                    directive set "/.../*mgc_mul_pipe(${i}?${j},*,2,0,2)" -match glob -QUANTITY 0
                    directive set "/.../*mgc_sqr_pipe(${i}?${j},*,2,0,2)" -match glob -QUANTITY 0
                }

                directive set "/.../*mgc_mul(1?${i}${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_mul(2?${i}${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr(1?${i}${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr(2?${i}${j},*)" -match glob -QUANTITY 0
                directive set "/.../*mgc_mul_pipe(1?${i}${j},*,2,0,1)" -match glob -QUANTITY 0
                directive set "/.../*mgc_mul_pipe(2?${i}${j},*,2,0,1)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr_pipe(1?${i}${j},*,2,0,1)" -match glob -QUANTITY 0
                directive set "/.../*mgc_sqr_pipe(2?${i}${j},*,2,0,1)" -match glob -QUANTITY 0
                
                if {$tech_type eq "45nm"} {
                    directive set "/.../*mgc_mul_pipe(1?${i}${j},*,2,0,2)" -match glob -QUANTITY 0
                    directive set "/.../*mgc_mul_pipe(2?${i}${j},*,2,0,2)" -match glob -QUANTITY 0
                    directive set "/.../*mgc_sqr_pipe(1?${i}${j},*,2,0,2)" -match glob -QUANTITY 0
                    directive set "/.../*mgc_sqr_pipe(2?${i}${j},*,2,0,2)" -match glob -QUANTITY 0
                }
            }
        }
    }
}

# Replace compile commands with compile_ultra in DC synthesis files
proc replace_compile_with_ultra {file_path} {
    # Check if file exists
    if {![file exists $file_path]} {
        puts "Error: File '$file_path' does not exist"
        return 0
    }
    
    # Get the directory and filename
    set file_dir [file dirname $file_path]
    set file_name [file tail $file_path]
    
    # Split filename into name and extension for backup naming
    set file_root [file rootname $file_name]
    set file_ext [file extension $file_name]
    set backup_name "${file_root}_original${file_ext}"
    set backup_path [file join $file_dir $backup_name]
    
    # Create backup copy
    if {[catch {file copy $file_path $backup_path} err]} {
        puts "Error creating backup: $err"
        return 0
    }
    puts "Created backup: $backup_path"
    
    # Read the file content
    if {[catch {
        set fp [open $file_path r]
        set content [read $fp]
        close $fp
    } err]} {
        puts "Error reading file: $err"
        return 0
    }
    
    # Define the regex pattern to match the compile block
    # Simpler pattern that matches the if-else compile block
    set compile_pattern {if\s*\{[^\}]*compatibility_version[^\}]*\}\s*\{[^\}]*compile\s+-map_effort[^\}]*\}\s*else\s*\{[^\}]*compile\s+-map_effort[^\}]*\}}
    
    set new_text "compile_ultra"
    
    # Perform the replacement using regex
    set replacement_count [regsub $compile_pattern $content $new_text new_content]
    
    # Check if replacement was made
    if {$replacement_count == 0} {
        puts "Warning: No replacement was made. The target pattern was not found."
        return 0
    } elseif {$replacement_count == 1} {
        puts "Info: compile_ultra replacement was made."
    } else {
        puts "Info: Unexpected replacements ($replacement_count) were made."
        exit
    }
    
    # Write the modified content back to the file
    if {[catch {
        set fp [open $file_path w]
        puts -nonewline $fp $new_content
        close $fp
    } err]} {
        puts "Error writing file: $err"
        return 0
    }
    
    puts "Successfully replaced compile commands with compile_ultra in $file_path"
    return 1
}

