# catapult_mul_asic.tcl
# ASIC-only sweep script for mul group (mul_f)

# lassign $argv kernel
set kernel mul_f

# Import utilities
set root_dir [file normalize [file dirname [info script]]]
source [file join $root_dir utils util.tcl]
set kernel_dir [file join $root_dir $kernel]
set tech_lib_dir [file normalize "$root_dir/../../gf12_libs"]
set techlib_db_path "/ip/arm/gf12/sc7p5mcpp84_base_slvt_c14/r1p0/db"
set custom_dc_script_path [file normalize "$root_dir/dc_custom_scripts"]

# move to a kernel/Catapult as working dir
set work_dir [enter_kernel_dir $root_dir $kernel]

# Sweep parameters
set bitwidths {64 192 256}
set target_iis {1}
set target_clocks {1 1.5 2}
set mul_types {sb kar nor}

# Solution-level parameters
set base_mul_depths_pow2 {128 16}
set base_mul_depths_nonpow2 {192 24}

# Karatsuba depth map
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


set include_dirs {
    utils/include
    mul_f/include
    sq_f/include
}
lappend include_dirs "$kernel/include"
set include_flags [build_include_flags $root_dir $include_dirs]
foreach mul_type $mul_types {
    foreach clk $target_clocks {
        foreach target_ii $target_iis {
            foreach bitwidth $bitwidths {
                # Call the core ASIC sweep logic for each configuration
                source [file join $root_dir catapult_mul_core_asic.tcl] 
            }
        }
    }
}
