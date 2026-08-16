proc set_tech_lib {tech_type root_dir lib_path lib_name vendor technology {lib_file ""}} {
    solution library remove *
    options set Flows/DesignCompiler/CustomScriptDirPath \
        [file normalize "$root_dir/dc_custom_scripts"]

    if {$tech_type eq "45nm"} {
        options set ComponentLibs/TechLibSearchPath $lib_path -append

        solution library add $lib_name \
            -- -rtlsyntool DesignCompiler -vendor $vendor -technology $technology
    } elseif {$tech_type eq "gf12_highperf"} {
        options set /ComponentLibs/TechLibSearchPath $lib_path/db  -append
        options set /ComponentLibs/TechLibSearchPath $lib_path/lef -append
        options set /ComponentLibs/TechLibSearchPath $lib_path/lib -append

        solution options set ComponentLibs/SearchPath [file dirname $lib_file] -append
        solution library add $lib_name \
            -- -rtlsyntool DesignCompiler -vendor $vendor -technology $technology
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
# Add each packaged RTL and turn the generated headers into blackboxes.
# Without BLACKBOX_FLOW the headers fall back to the real implementation.
proc add_blackbox_rtl { design_build_dir } {
    set rtl_files [glob -nocomplain [file join $design_build_dir blackbox *.v]]
    if {[llength $rtl_files] == 0} {
        return
    }
    foreach rtl $rtl_files {
        solution file add $rtl -type verilog -exclude true
    }
    options set Input/CompilerFlags "[options get Input/CompilerFlags] -DBLACKBOX_FLOW"
}

# The scheduled latency is final at the schedule stage, so the design does
# not have to run to extract to know how many cycles it takes.
proc latency_is_one { design_build_dir } {
    set latency [solution get /DATUM/FIELDS/timing/COLUMNS/tm_latency_cycles/VALUE]
    set fp [open [file join $design_build_dir Catapult latency.txt] w]
    puts $fp $latency
    close $fp
    return [expr {$latency <= 1}]
}
