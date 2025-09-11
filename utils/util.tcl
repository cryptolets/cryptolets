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
    options set Flows/Vivado/XILINX_VIVADO /eda/xilinx//Vivado/2024.2/
    options set Flows/SCVerify/MAX_ERROR_CNT 1
}

proc set_tech_lib {tech_type root_dir} {
    if {$tech_type eq "asic"} {
        solution library add nangate-45nm_beh \
            -- -rtlsyntool OasysRTL -vendor Nangate -technology 045nm
    } elseif {$tech_type eq "asicgf12"} {
        solution library remove *
        solution library add sc7p5mcpp84_12lp_base_slvt_c14_tt_nominal_max_0p90v_25c_dc \
            -file "$root_dir/../gf12/sc7p5mcpp84_12lp_base_slvt_c14_tt_nominal_max_0p90v_25c_dc_smooth.lib" \
            -- -rtlsyntool DesignCompiler -vendor GlobalFoundries -technology 012nm
    } else {
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

proc handle_base_mul_depths {mul_type bitwidth base_mul_depths_pow2 base_mul_depths_nonpow2} {
    if {[expr {($bitwidth & ($bitwidth - 1)) == 0}]} {
        return $base_mul_depths_pow2
    } else {
        return $base_mul_depths_nonpow2
    }
}

proc handle_kar_depths {mul_type bitwidth kar_mul_depth_map} {
    if {$mul_type eq "kar"} {
        return [dict get $kar_mul_depth_map $bitwidth]
    } else {
        return [list $bitwidth]
    }
}

proc run_osci_test {kernel_dir work_dir bitwidth NUM_TEST_SAMPLES TEST GEN_SAMPLES} {
    # generate samples csv file and run initial C++ tests
    if {$TEST} {
        set outputs_dir [file join $work_dir outputs]
        if {![file isdirectory $outputs_dir]} {
            file mkdir $outputs_dir
        }

        set sample_fp [file join $work_dir samples/samples_${bitwidth}.csv]
        set output_fp [file join $outputs_dir output_${bitwidth}.csv]
        set golden_fp [file join $work_dir goldens/golden_${bitwidth}.csv]

        if {$GEN_SAMPLES} {
            set cmd [list python3 [file join $kernel_dir gen_samples.py] \
                    --bw $bitwidth \
                    --n $NUM_TEST_SAMPLES]

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
        set sample_fp [file join $work_dir samples/samples_${bitwidth}.csv]
        set output_fp [file join $work_dir outputs/output_${bitwidth}.csv]
        set golden_fp [file join $work_dir goldens/golden_${bitwidth}.csv]

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

proc run_syn {tech_type SYN} {
    if {$SYN} {
        if {$tech_type eq "fpga"} {
            puts "Syn: Running FPGA Vivado synthesis"
            go synthesize
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

proc remove_broken_mul_libs { tech_type } {
    # Make sure mgc_mul's with blank MinClkPrd are not used

    # Don't use mgc_mul or mgc_sqr > 64b, up till 2999b
    for {set i 5} {$i <= 9} {incr i 1} {
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

    # 3-digit numbers >=201
    # if {$tech_type eq "asic"} {
    #     for {set i 2} {$i <= 9} {incr i 1} {
    #         directive set "/.../*mgc_mul(${i}??,*,1)" -match glob -QUANTITY 0
    #         directive set "/.../*mgc_mul(${i}??,*,2)" -match glob -QUANTITY 0
    #         directive set "/.../*mgc_mul(${i}??,*,6)" -match glob -QUANTITY 0
    #     }

    #     # 1000 <= num < 2000
    #     directive set "/.../*mgc_mul(1???,*,1)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(1???,*,2)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(1???,*,6)" -match glob -QUANTITY 0

    #     # for mul + reduction where output bw = in bw
    #     directive set "/.../*mgc_mul(256,0,256,0,256,3)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(256,0,256,0,256,6)" -match glob -QUANTITY -1

    #     directive set "/.../*mgc_mul(384,0,384,0,384,3)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(384,0,384,0,384,5)" -match glob -QUANTITY 0

    #     directive set "/.../*mgc_mul(512,0,512,0,512,3)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(512,0,512,0,512,5)" -match glob -QUANTITY 0

    #     directive set "/.../*mgc_mul(768,0,768,0,768,3)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(768,0,768,0,768,5)" -match glob -QUANTITY 0

    #     directive set "/.../*mgc_mul(1024,0,1024,0,1024,3)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(1024,0,1024,0,1024,5)" -match glob -QUANTITY 0

    #     # TODO: add for mgc_sqr

    # } elseif {$tech_type eq "asicgf12"} {
    #     # same for reduced and non-reduced
    #     # 200 <= num < 300
    #     directive set "/.../*mgc_mul(2??,*,1)" -match glob -QUANTITY 0

    #     # 300 <= num < 1000
    #     for {set i 3} {$i <= 9} {incr i 1} {
    #         directive set "/.../*mgc_mul(${i}??,*,1)" -match glob -QUANTITY 0
    #         directive set "/.../*mgc_mul(${i}??,*,2)" -match glob -QUANTITY 0
    #     }

    #     # 1000 <= num < 2000
    #     directive set "/.../*mgc_mul(1???,*,1)" -match glob -QUANTITY 0
    #     directive set "/.../*mgc_mul(1???,*,2)" -match glob -QUANTITY 0

    #     # TODO: add for mgc_sqr
    # }
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
