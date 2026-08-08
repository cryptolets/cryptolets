# TODO: Integrate later
proc inject_threads_vivado {syn_file_pat threads_per_process} {
    # Read file
    set fh [open $syn_file_path r]
    set content [read $fh]
    close $fh

    # Block to inject
    set thread_block "# --- injected by Catapult wrapper ---
set_param general.maxThreads $threads_per_process
set_param synth.maxThreads   $threads_per_process
puts \"MAX THREADS: general=\[get_param general.maxThreads\] synth=\[get_param synth.maxThreads\]\"
# --- end injection ---"

    # Prepend
    set new_content "$thread_block\n\n$content"

    # Write back
    set fh [open $syn_file_path w]
    puts $fh $new_content
    close $fh
}

proc run_fpga_syn {tech_type threads_per_process} {
    if {[is_fpga $tech_type]} {
        puts "Running FPGA synthesis with Vivado"

        # Fixes issue with running Vivado for Versal HBM fpga (TODO: check if still an issue)
        set ::env(LD_LIBRARY_PATH) "/eda/xilinx/Vivado/2024.2/lib/lnx64.o"
        catch {unset ::env(LD_PRELOAD)}
        puts "LD_LIBRARY_PATH is now: $::env(LD_LIBRARY_PATH)"

        set syn_file_path [file join [solution get /SOLUTION_DIR] "vivado_v" "rtl.v.xv"]
        inject_threads_vivado $syn_file_path $threads_per_process

        if {[catch {flow run /Vivado/synthesize -shell $syn_file_path} err]} {
            puts "ERROR: FPGA Vivado synthesis failed -> $err"
            return -code error $err
        }
    }
}