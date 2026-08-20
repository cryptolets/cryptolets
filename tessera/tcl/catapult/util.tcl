proc set_tech_lib {tech_type root_dir lib_path lib_name vendor technology \
                   {lib_file ""} {family ""} {speed ""} {part ""}} {
    solution library remove *
    options set Flows/DesignCompiler/CustomScriptDirPath \
        [file normalize "$root_dir/dc_custom_scripts"]

    # An FPGA names a part, and Vivado synthesizes it during this run
    if {[is_fpga $tech_type]} {
        solution library add $lib_name \
            -- -rtlsyntool Vivado -manufacturer $vendor \
            -family $family -speed $speed -part $part
        return
    }

    # A cell library is found by its files, which differ per vendor
    if {$lib_path ne ""} {
        foreach sub {"" db lef lib} {
            options set /ComponentLibs/TechLibSearchPath \
                [file join $lib_path $sub] -append
        }
    }
    if {$lib_file ne ""} {
        solution options set ComponentLibs/SearchPath [file dirname $lib_file] -append
    }

    solution library add $lib_name \
        -- -rtlsyntool DesignCompiler -vendor $vendor -technology $technology
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
        directive set -CLUSTER_CSA_ARCH dadda ;# wordwise, dadda, wallace
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
