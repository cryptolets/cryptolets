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
    }
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

proc set_ii { ii {multi_word 0} } {
    if {!$multi_word} {
        directive set -PIPELINE_INIT_INTERVAL $ii
    }
}

proc save_table { table_fp } {
    solution table export -file $table_fp
}