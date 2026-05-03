proc init_options {} {
    options defaults
    options set /Input/CppStandard c++14
    options set /Input/TargetPlatform x86_64
    options set Output/OutputVHDL false ;# we want only verilog output
    options set Output/RTLSchem false ;# rtl schematics take up a ton of space
    options set Flows/SCVerify/MAX_ERROR_CNT 1
    options set Flows/DesignCompiler/OutNetlistFormat verilog
    options set Flows/Vivado/XILINX_VIVADO /eda/xilinx//Vivado/2024.2/
}


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


proc set_tech_lib {tech_type root_dir} {    
    solution library remove *
    if {$tech_type eq "45nm"} {
        set custom_dc_script_path [file normalize "$root_dir/dc_custom_scripts"]
        options set Flows/DesignCompiler/CustomScriptDirPath "$custom_dc_script_path"
        options set ComponentLibs/TechLibSearchPath [file normalize "$root_dir/../45nm_db"] -append

        solution library add nangate-45nm_beh \
            -- -rtlsyntool DesignCompiler -vendor Nangate -technology 045nm
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
            -file "$root_dir/../custom_fpga_catapult_libs/mgc_Xilinx-VERSAL-hbm-3HP_beh.lib" \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VERSAL-hbm -speed -3HP \
            -part xcvh1782-lsva4737-3HP-e-S
    } elseif {$tech_type eq "fpga_hbmvh1582_custom"} {
        # Versal HBM used in evaluation kit
        solution library add mgc_Xilinx-VERSAL-hbm-2MP_beh \
            -file "$root_dir/../custom_fpga_catapult_libs/mgc_Xilinx-VERSAL-hbm-2MP_beh.lib" \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VERSAL-hbm -speed -2MP \
            -part xcvh1582-vsva3697-2MP-e-S
    } elseif {$tech_type eq "fpga_vu9p_custom"} {
        # Virtex UltraScale+ used by other papers
        solution library add mgc_Xilinx-VIRTEX-uplus-2_beh \
            -file "$root_dir/../custom_fpga_catapult_libs/mgc_Xilinx-VIRTEX-uplus-2_beh.lib" \
            -- -rtlsyntool Vivado -manufacturer Xilinx \
            -family VIRTEX-uplus -speed -2 \
            -part xcvu9p-flga2104-2-i
    }
}

proc run_osci_test {test kernel_build_dir} {
    # run c++ tests with osci
    if {$test} {
        puts "Running C++ tests with osci"
        set proj_dir [project get /PROJECT_DIR]
        set sample_fp [file join $kernel_build_dir samples.csv]
        set output_fp [file join $proj_dir output.csv]
        set golden_fp [file join $kernel_build_dir golden.csv]

        flow package require /SCVerify
        flow package option set /SCVerify/INVOKE_ARGS "$sample_fp $output_fp"
        flow run /SCVerify/launch_make ./scverify/Verify_orig_cxx_osci.mk {} SIMTOOL=osci sim

        # check if golden and output match
        if {[catch {exec diff -q $golden_fp $output_fp}]} {
            puts "ERROR: Verifying C++ with osci"
            exit 1
        } else {
            puts "PASS: Output matches golden"
        }
    }
}


proc is_fpga {tech_type} {
    # all fpga tech types start with "fpga"
    return [string match "fpga*" $tech_type]
}

proc adder_tree_opt {tech_type} {
    if {![is_fpga $tech_type]} {
        directive set -CLUSTER addtree
        directive set -CLUSTER_FAST_MODE true
    }
}

proc set_ii { multi_word ii} {
    if {!$multi_word} {
        directive set -PIPELINE_INIT_INTERVAL $ii
    }
}

proc save_table { table_fp } {
    solution table export -file $table_fp
}

proc remove_broken_mul_libs { tech_type } {
    # Make sure mgc_mul's with blank MinClkPrd are not used

    if {![is_fpga $tech_type]} {
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