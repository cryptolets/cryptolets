# utils/util.tcl
# Common helper procs for Catapult

# Ensure kernel/Catapult dir exists and cd into it
proc enter_work_dir {kernel_dir} {
    set work_dir [file join $kernel_dir Catapult]
    if {![file exists $work_dir]} {
        file mkdir $work_dir
    }
    cd $work_dir
    return $work_dir
}

proc override_default_options {} {
    options defaults
    options set /Input/CppStandard c++14
    options set /Input/TargetPlatform x86_64
    options set Flows/SCVerify/MAX_ERROR_CNT 1
}

proc set_tech_lib {tech_type root_dir} {
    solution library remove *
    if {$tech_type eq "45nm"} {
        solution library add nangate-45nm_beh \
            -- -rtlsyntool OasysRTL -vendor Nangate -technology 045nm
    } elseif {$tech_type eq "gf12"} {
        set custom_dc_script_path [file normalize "$root_dir/dc_custom_scripts"]
        options set Flows/DesignCompiler/CustomScriptDirPath "$custom_dc_script_path"
        options set ComponentLibs/TechLibSearchPath "/ip/arm/gf12/sc7p5mcpp84_base_slvt_c14/r1p0/db" -append

        solution library add sc7p5mcpp84_12lp_base_slvt_c14_tt_nominal_max_0p90v_25c_dc \
            -file "$root_dir/../gf12_libs/sc7p5mcpp84_12lp_base_slvt_c14_tt_nominal_max_0p90v_25c_dc_smooth.lib" \
            -- -rtlsyntool DesignCompiler -vendor GlobalFoundries -technology 012nm

    } elseif {$tech_type eq "saed32"} {
        # add custom dc script path
        set custom_dc_script_path [file normalize "$root_dir/dc_custom_scripts"]
        options set Flows/DesignCompiler/CustomScriptDirPath "$custom_dc_script_path"
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/tech/tf" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/lib/stdcell_lvt/lef" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/lib/stdcell_lvt/db_nldm" -append
        options set ComponentLibs/TechLibSearchPath "/ip/synopsys/saed32/v02_2024/lib/stdcell_lvt/db_ccs" -append

        solution library add saed32lvt_tt0p78v125c_beh \
            -- -rtlsyntool DesignCompiler -vendor SAED32 -technology {lvt tt0p78v125c}        
    } else {
        options set Flows/Vivado/XILINX_VIVADO /eda/xilinx//Vivado/2024.2/
        
        solution library add mgc_Xilinx-VIRTEX-uplus-1_beh \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VIRTEX-uplus -speed -1 \
            -part xcvu9p-flga2104-1-e
    }
}

# Project handling
proc open_or_create_proj {proj_name work_dir} {
    set proj_ccs [file join $work_dir "${proj_name}.ccs"]
    set proj_dir [file join $work_dir $proj_name]

    if {[file exists $proj_ccs]} {
        puts "Opening existing project: $proj_name"
        project load $proj_ccs
    } else {
        puts "Creating new project at: $proj_name"
        project new -name $proj_name -directory $proj_dir
        project save
    }
}

# Solution handling
proc open_or_create_solution {sol_name} {
    if {[catch {solution new -state new $sol_name} err]} {
        puts "Creating new solution: $sol_name"
        solution new $sol_name
    } else {
        puts "Opened existing solution: $sol_name"
    }
}

# Clock constraints
proc set_clock {period} {
    set clk_high_time [expr {$period / 2}]
    set clk_uncertainty [expr {$period * 0}]

    directive set -CLOCKS [
        list clk [list \
            -CLOCK_PERIOD $period \
            -CLOCK_UNCERTAINTY $clk_uncertainty \
            -CLOCK_HIGH_TIME $clk_high_time \
        ]
    ]
}

# Build include flags from list of include dirs
proc build_include_flags {root_dir include_dirs} {
    set include_flags ""
    foreach dir $include_dirs {
        append include_flags " -I[file join $root_dir $dir]"
    }
    return $include_flags
}

proc handle_kar_depths {mul_type bitwidth kar_mul_depth_map} {
    if {$mul_type eq "kar"} {
        return [dict get $kar_mul_depth_map $bitwidth]
    } else {
        return [list $bitwidth]
    }
}

proc run_gen_field_const {bitwidth curve_type root_dir} {
    if {$curve_type eq "RAND_CURVE"} {
        set proj_dir [project get /PROJECT_DIR]
        set py_exec [file join $root_dir .venv/bin/ python]
        set py_file [file join $root_dir utils gen_field_const.py]
        set json_file [file join $proj_dir field_const.json]
        set cmd [list $py_exec $py_file --bitwidth $bitwidth --json-file $json_file]
        exec tcsh -c "$cmd"
    }
}

proc run_osci_test {kernel_dir work_dir root_dir bitwidth NUM_TEST_SAMPLES TEST GEN_SAMPLES {curve_type ""}} {
    # generate samples csv file and run initial C++ tests
    if {$TEST} {
        set proj_dir [project get /PROJECT_DIR]
        set outputs_dir [file join $proj_dir outputs]
        if {![file isdirectory $outputs_dir]} {
            file mkdir $outputs_dir
        }

        set sample_fp [file join $proj_dir samples/samples_${bitwidth}.csv]
        set output_fp [file join $outputs_dir output_${bitwidth}.csv]
        set golden_fp [file join $proj_dir goldens/golden_${bitwidth}.csv]

        if {$GEN_SAMPLES} {
            set py_exec [file join $root_dir .venv/bin/ python]
            set cmd [list $py_exec [file join $kernel_dir gen_samples.py] \
              --bw $bitwidth \
              --n $NUM_TEST_SAMPLES \
              --samples-file $sample_fp \
              --golden-file $golden_fp]

            if {$curve_type ne ""} {
                if {$curve_type ne "RAND_CURVE"} {
                    set json_file [file join $root_dir field_const.json]
                } else {
                    set json_file [file join $proj_dir field_const.json]
                }

                lappend cmd --curve_type $curve_type
                lappend cmd --json-file $json_file
            }

            exec tcsh -c "$cmd"
        }

        flow package require /SCVerify
        flow package option set /SCVerify/INVOKE_ARGS "$sample_fp $output_fp"
        flow run /SCVerify/launch_make ./scverify/Verify_orig_cxx_osci.mk {} SIMTOOL=osci sim

        # check if golden and output match
        if {[catch {exec diff -q $golden_fp $output_fp}]} {
            puts "ERROR: Verifying C++ with osci bitwidth=$bitwidth"
            exit 1
        } else {
            puts "PASS: Output matches golden for bitwidth=$bitwidth"
        }
    }

}

proc run_scverify {kernel_dir work_dir bitwidth SIM} {
    if {$SIM} {
        puts "Sim: Running SCVerify for bitwidth=$bitwidth"
        set proj_dir [project get /PROJECT_DIR]
        set sample_fp [file join $proj_dir samples/samples_${bitwidth}.csv]
        set output_fp [file join $proj_dir outputs/output_${bitwidth}.csv]
        set golden_fp [file join $proj_dir goldens/golden_${bitwidth}.csv]

        flow package require /SCVerify
        flow package option set /SCVerify/INVOKE_ARGS "$sample_fp $output_fp"
        flow run /SCVerify/launch_make ./scverify/Verify_rtl_v_msim.mk {} SIMTOOL=msim sim

        if {[catch {exec diff -q $golden_fp $output_fp}]} {
            puts "ERROR: Verifying with SCVerify bitwidth=$bitwidth"
            exit 1
        } else {
            puts "PASS: Output matches golden for bitwidth=$bitwidth"
        }
    }
}

proc run_syn {tech_type SYN root_dir {RTL_FILE "rtl"}} {
    if {$SYN} {
        if {$tech_type eq "fpga"} {
            puts "Syn: Running FPGA Vivado synthesis"
            go synthesize
        } elseif {$tech_type eq "saed32" || $tech_type eq "gf12"} {
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
            flow run /DesignCompiler/dc_shell ./$RTL_FILE.v.dc
        }
    }
}

proc branch_if_ccore_comb {kernel} {
    set latency_cycles [solution get /DATUM/FIELDS/timing/COLUMNS/tm_latency_cycles/VALUE]
    if {$latency_cycles == 0} {
        set old_sol "[solution get /name].[solution get /VERSION]"
        # for combinational
        go libraries
        solution design set $kernel -combinational
        go architect
        # solution remove -solution $old_sol -delete ;# commented because causes problems with loading proj
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

proc get_q_val {q_type} {
    if {$q_type eq "fixedq"} {
        return "FIXED_Q"
    } else {
        return "VAR_Q"
    }
}

proc get_mul_val {mul_type} {
    if {$mul_type eq "kar"} {
        return "MUL_KARATSUBA"
    } elseif {$mul_type eq "sb"} {
        return "MUL_SCHOOLBOOK"
    } else {
        return "MUL_NORMAL"
    }
}

proc remove_broken_mul_libs { tech_type } {
    # Make sure mgc_mul's with blank MinClkPrd are not used

    # Don't use mgc_mul or mgc_sqr > 64b, up till 2999b
    for {set i 7} {$i <= 9} {incr i 1} {
        directive set "/.../*mgc_mul(${i}?,*)" -match glob -QUANTITY 0
        directive set "/.../*mgc_mul(${i}?,*)" -match glob -QUANTITY 0
        directive set "/.../*mgc_sqr(${i}?,*)" -match glob -QUANTITY 0
        directive set "/.../*mgc_sqr(${i}?,*)" -match glob -QUANTITY 0
    }

    for {set i 1} {$i <= 9} {incr i 1} {
        directive set "/.../*mgc_mul(${i}??,*)" -match glob -QUANTITY 0
        directive set "/.../*mgc_mul(${i}??,*)" -match glob -QUANTITY 0
        directive set "/.../*mgc_sqr(${i}??,*)" -match glob -QUANTITY 0
        directive set "/.../*mgc_sqr(${i}??,*)" -match glob -QUANTITY 0
    }

    directive set "/.../*mgc_mul(1???,*)" -match glob -QUANTITY 0
    directive set "/.../*mgc_mul(2???,*)" -match glob -QUANTITY 0
    directive set "/.../*mgc_sqr(1???,*)" -match glob -QUANTITY 0
    directive set "/.../*mgc_sqr(2???,*)" -match glob -QUANTITY 0
}

# proc create_lib_f {kernel_dir lib_name} {
#     set lib_dir [file join $kernel_dir lib]
#     if {![file exists $lib_dir]} {
#         file mkdir $lib_dir
#     }
#     set lib_fp [file join $lib_dir $lib_name]
#     solution netlist -library -replace $lib_fp
#     return $lib_fp
# }

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

