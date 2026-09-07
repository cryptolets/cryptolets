proc run_osci_test {test test_cpp_only design_build_dir} {
    # run c++ tests with osci
    if {$test} {
        puts "Running C++ tests with osci"
        set sample_fp [file join $design_build_dir test samples.csv]
        set output_fp [file join $design_build_dir test outputs_cpp.csv]
        set golden_fp [file join $design_build_dir test goldens.csv]

        flow package require /SCVerify
        flow package option set /SCVerify/INVOKE_ARGS "$sample_fp $output_fp"
        flow run /SCVerify/launch_make ./scverify/Verify_orig_cxx_osci.mk {} SIMTOOL=osci sim

        # check if golden and output match
        set diff_result [catch {exec diff -q $golden_fp $output_fp} diff_output]
        if {$diff_result != 0} {
            puts "ERROR: Verifying C++ with osci"
            puts "  diff output: $diff_output"
            exit 1
        } else {
            puts "PASS: Output matches golden"
        }
    }

    # If test_cpp_only is true, exit after testing C++ code with osci
    if {$test_cpp_only} {
        puts "Exiting after testing C++ code only"
        exit 0
    }
}

proc run_verify_rtl {verify_rtl design_build_dir} {
    global uses_blackboxes
    global dware_dir
    # Run VSC RTL Simulation and Verification
    if {$verify_rtl} {
        puts "Running Questa RTL simulation and verification"
        set sample_fp [file join $design_build_dir test samples.csv]
        set output_fp [file join $design_build_dir test outputs_rtl.csv]
        set golden_fp [file join $design_build_dir test goldens.csv]

        flow package require /SCVerify
        flow package option set /SCVerify/INVOKE_ARGS "$sample_fp $output_fp"
        # A blackboxed dependency arrives as RTL that already names the vendor
        # arithmetic, and catapult only builds models for arithmetic it mapped
        # itself, so the models built for the kernel are named here
        set args SIMTOOL=msim
        if { $uses_blackboxes } {
            set dw $dware_dir
            lappend args "ADDED_VLOGLIBS=$dw/DW01_ver $dw/DW02_ver $dw/DW03_ver $dw/DWARE_ver"
        }
        flow run /SCVerify/launch_make ./scverify/Verify_rtl_v_msim.mk {} {*}$args sim

        if {[catch {exec diff -q $golden_fp $output_fp}]} {
            puts "ERROR: Verifying with SCVerify"
            exit 1
        } else {
            puts "PASS: Output matches golden"
        }
    }
}
