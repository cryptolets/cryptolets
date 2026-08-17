proc inject_threads_vivado {syn_file_path threads_per_process} {
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

        # Vivado loads its own libraries, and an inherited preload breaks it
        set ::env(LD_LIBRARY_PATH) [file join $::tool_vivado lib lnx64.o]
        catch {unset ::env(LD_PRELOAD)}

        set syn_file_path [file join [solution get /SOLUTION_DIR] "vivado_v" "rtl.v.xv"]
        inject_threads_vivado $syn_file_path $threads_per_process

        if {[catch {flow run /Vivado/synthesize -shell $syn_file_path} err]} {
            puts "ERROR: FPGA Vivado synthesis failed -> $err"
            return -code error $err
        }
    }
}