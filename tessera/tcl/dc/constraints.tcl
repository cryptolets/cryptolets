# Timing constraints for synthesis. The same contract is put on every design,
# so their numbers compare, rather than the one Catapult estimated with.

# The power estimate assumes every input toggles half the time
proc set_activity {} {
    set input_ports [remove_from_collection [all_inputs] [get_ports -quiet clk]]
    set_switching_activity [get_ports $input_ports] -static_probability 0.5 -toggle_rate 0.5
    infer_switching_activity -apply
}

# A sequential design runs on its clk port
proc set_clocked_constraints {period} {
    create_clock clk -name clk -period $period

    set input_ports  [remove_from_collection [all_inputs] clk]
    set output_ports [all_outputs]

    # Inputs arrive at the clock edge. Fine for an architecture study, not
    # for a tapeout, where the driver's delay would count
    set_input_delay  -max 0 [get_ports $input_ports] -clock clk
    set_input_delay  -min 0 [get_ports $input_ports] -clock clk

    set_output_delay -max [expr {$period / 4.0}] [get_ports $output_ports] -clock clk
    set_output_delay -min [expr {$period / 8.0}] [get_ports $output_ports] -clock clk

    group_path -name output_group -to   [all_outputs]
    group_path -name input_group  -from [all_inputs]

    set_activity
}

# A combinational design (a CCORE) has no clock: the whole period is its
# input to output budget, against a virtual clock, as Catapult constrains it
proc set_comb_constraints {period} {
    create_clock -name clk -period $period

    set_input_delay  0 [all_inputs]  -clock clk
    set_output_delay 0 [all_outputs] -clock clk
    set_max_delay $period -from [all_inputs] -to [all_outputs]

    set_activity
}
