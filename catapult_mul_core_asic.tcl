# catapult_mul_core_asic.tcl
# Core ASIC-only sweep logic for mul group (mul_f)
# This script is intended to be sourced inside the foreach loop of catapult_mul_asic.tcl

# Assumes the following variables are set in the parent script:
#   bitwidth, target_ii, mul_type, clk, root_dir, kernel, kernel_dir, work_dir, include_flags, tech_lib_dir
#   base_mul_depths_pow2, base_mul_depths_nonpow2, kar_mul_depth_map, CCORE_MULS

# Skip logic for mul_type 'nor'
if {$mul_type eq "nor"} {
    if {$bitwidth > 128} {
        if { !($bitwidth == 192 && $clk > 0.33) } {
            puts "Skipped: bitwidth=$bitwidth because >128-bit for normal, and not 192-bit with >0.33ns clock"
            return
        }
    }
}

# Reset tool options
options defaults
options set /Input/CppStandard c++14
options set /Input/TargetPlatform x86_64
options set Flows/DesignCompiler/OutNetlistFormat verilog

set proj_name "Catapult_${bitwidth}_asic_ii${target_ii}_${mul_type}_${clk}ns"
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

puts "\n=== Starting project $proj_name ==="

# different base_mul_depths for pow2 bitwidths and bitwidths like, 96,192,384,etc.
if {[expr {($bitwidth & ($bitwidth - 1)) == 0}]} {
    set base_mul_depths $base_mul_depths_pow2
} else {
    set base_mul_depths $base_mul_depths_nonpow2
}

foreach bm $base_mul_depths {
    if {$mul_type eq "kar"} {
        set kar_depths [dict get $kar_mul_depth_map $bitwidth]
    } else {
        set kar_depths {0}
    }

    foreach kar $kar_depths {
        set sol_name "sol_bm${bm}_kar${kar}"
        open_or_create_solution $sol_name
        puts "  -> Solution: $sol_name (bitwidth=$bitwidth, bm=$bm, kar=$kar)"

        # Compiler flags
        set mul_val [expr {
            $mul_type eq "kar" ? "MUL_KARATSUBA" :
            ($mul_type eq "sb" ? "MUL_SCHOOLBOOK" : "MUL_NORMAL")
        }]

        set flags ""
        append flags " -DBITWIDTH=$bitwidth"
        append flags " -DMUL_TYPE=$mul_val"
        append flags " -DKAR_BASE_MUL_WIDTH=$kar"
        append flags " -DBASE_MUL_WIDTH=$bm"

        if {$CCORE_MULS} {
            append flags " -DCCORE_MULS=1"
        }

        options set /Input/CompilerFlags "$include_flags $flags"

        # add design compiler library path
        options set ComponentLibs/TechLibSearchPath "$techlib_db_path" -append

        # add custom dc script path
        options set Flows/DesignCompiler/CustomScriptDirPath "$custom_dc_script_path"

        # this doesnt work
        # set number of cores to be used by DesignCompiler
        # options set Flows/DesignCompiler/MaxCores 4

        # Add kernel + dependencies
        solution file add $kernel_dir/src/${kernel}.cpp
        solution file add $kernel_dir/src/${kernel}_tb.cpp -exclude true
        solution file add [file join $root_dir utils/src/csvparser.cpp] -exclude true

        # add lib file path
        solution options set ComponentLibs/SearchPath "$tech_lib_dir" -append

        go analyze
        solution design set $kernel -top
        go compile

        # ASIC library only
        solution library add sc7p5mcpp84_12lp_base_slvt_c14_tt_nominal_max_0p90v_25c_dc \
                            -- -rtlsyntool DesignCompiler -vendor GlobalFoundries -technology 012nm

        go libraries

        set_clock $clk
        go assembly

        directive set -PIPELINE_INIT_INTERVAL $target_ii
        directive set -DESIGN_GOAL latency
        # directive set SCHED_USE_MULTICYCLE true

        go architect
        if {$bitwidth == 192} {
            # Only use non-pipelined muls for 192-bit, pipelined have 0 delay issue
            directive set /.../*mgc_mul(*) -match glob -QUANTITY -1
            directive set /.../*mgc_mul_pipe(*) -match glob -QUANTITY 0
        }

        go extract

        set table_name "table_bw${bitwidth}_ttasic_ii${target_ii}_mt${mul_type}_f${clk}ns.csv"
        solution table export -file [file join $work_dir $table_name]

        project save

        # Replace compile commands with compile_ultra in the DC synthesis file
        # Get the full path to the generated DC file
        set version [solution get \VERSION]

        set dc_file_path [file join $proj_dir "${sol_name}.${version}" "${RTL_FILE}.v.dc"]
        if {[file exists $dc_file_path]} {
            replace_compile_with_ultra $dc_file_path
        } else {
            puts "Warning: DC file not found at $dc_file_path"
            continue
        }

        flow run /DesignCompiler/dc_shell ./$RTL_FILE.v.dc
    }
}

