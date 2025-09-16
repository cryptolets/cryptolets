# catapult_mul_single_config.tcl
# Single configuration script for mul_f synthesis
# Reads configuration from environment variables set by the bash script

# Read configuration from environment variables
if {![info exists env(MUL_TYPE)] || ![info exists env(CLK)] || 
    ![info exists env(TARGET_II)] || ![info exists env(BITWIDTH)]} {
    puts "Error: Required environment variables not set"
    puts "Required: MUL_TYPE, CLK, TARGET_II, BITWIDTH"
    exit 1
}

set mul_type $env(MUL_TYPE)
set clk $env(CLK)
set target_ii $env(TARGET_II)
set bitwidth $env(BITWIDTH)

# Get Design Compiler core allocation if available
set dc_cores 1
if {[info exists env(DC_CORES)]} {
    set dc_cores $env(DC_CORES)
}

puts "=== Single Configuration Synthesis ==="
puts "Configuration: mul_type=$mul_type, clk=${clk}ns, ii=$target_ii, bitwidth=${bitwidth}bit"
puts "Design Compiler cores: $dc_cores"
puts "========================================="

# Set kernel (same as original)
set kernel mul_f

# Import utilities and set paths (same as original)
set root_dir [file normalize [file dirname [info script]]]
source [file join $root_dir utils util.tcl]
set kernel_dir [file join $root_dir $kernel]
set tech_lib_dir [file normalize "$root_dir/../../gf12_libs"]
set techlib_db_path "/ip/arm/gf12/sc7p5mcpp84_base_slvt_c14/r1p0/db"
set custom_dc_script_path [file normalize "$root_dir/dc_custom_scripts"]

# Move to kernel/Catapult as working dir
set work_dir [enter_kernel_dir $root_dir $kernel]

# Set parameters (same as original)
set base_mul_depths_pow2 {128 16}
set base_mul_depths_nonpow2 {192 24}

set kar_mul_depth_map {
    32 {32 16}
    64 {64 32 16}
    128 {128 64 32 16}
    192 {192 96 48 24}
    256 {128 64 32 16}
}

set CCORE_MULS true

# Control flags
set SIM false
set SYN false
set USE_CONCAT_RTL 0

if {$USE_CONCAT_RTL == 1} {
    set RTL_FILE concat_rtl
} else {
    set RTL_FILE rtl
}

set env(rtl_file) $RTL_FILE

# Set include directories and flags
set include_dirs {
    utils/include
    mul_f/include
    sq_f/include
}
lappend include_dirs "$kernel/include"
set include_flags [build_include_flags $root_dir $include_dirs]

# Set Design Compiler core usage for this process
# This will be used in the core ASIC script
set DC_MAX_CORES $dc_cores

puts "Starting synthesis for configuration:"
puts "  mul_type: $mul_type"
puts "  clock: ${clk}ns"
puts "  target_ii: $target_ii"
puts "  bitwidth: $bitwidth"
puts "  DC cores: $dc_cores"
puts ""

# Source the core ASIC sweep logic with the single configuration
source [file join $root_dir catapult_mul_core_asic.tcl]

puts ""
puts "=== Synthesis completed for configuration ==="
puts "mul_type=$mul_type, clk=${clk}ns, ii=$target_ii, bitwidth=${bitwidth}bit"
puts "============================================="
