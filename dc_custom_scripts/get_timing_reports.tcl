puts "Timing reporting started "
set clk_candidates {0 INOUT clk clk 1 IN x_rsc_dat x_rsc_dat 2 IN y_rsc_dat y_rsc_dat} 
set i_candidates {1 IN x_rsc_dat x_rsc_dat 2 IN y_rsc_dat y_rsc_dat} 
set o_candidates {3 OUT return_rsc_dat return_rsc_dat 1 IN x_triosy_lz x_triosy_lz 2 IN y_triosy_lz y_triosy_lz 3 OUT return_triosy_lz return_triosy_lz} 
foreach { orsid orsmode iclk ote } $clk_candidates {
puts "Timing reporting for orsid=$orsid orsmode=$orsmode iclk=$iclk ote=$ote "
    foreach { irsid irsmode iport ite } $i_candidates {
        if { [llength [get_clocks -quiet $iclk] ] > 0 && [llength [all_registers -clock $iclk ] ] > 0 } {
        puts "-- Synthesis input_to_register:timing report for design 'mul_f' '${irsid}' '${irsmode}' port '${ite}' '${orsid}' '${orsmode}' CLOCK '${ote}'"
        report_timing -nosplit -significant_digits 6 -capacitance -from ${iport} -to [all_registers -data_pins -clock $iclk ] 
        puts "-- END Synthesis input_to_register:timing report for design 'mul_f' '${irsid}' '${irsmode}' port '${ite}' '${orsid}' '${orsmode}' CLOCK '${ote}'"
        }
    }
}
foreach { orsid orsmode oclk ote } $clk_candidates {
    foreach { irsid irsmode iclk ite } $clk_candidates {
        if { [llength [get_clocks -quiet ${iclk}] ] > 0 && [llength [get_clocks -quiet ${oclk}] ] > 0 && [llength [all_registers -clock ${iclk}] ] > 0 && [llength [all_registers -clock ${oclk}] ] > 0 } {
        puts "-- Synthesis register_to_register:timing report for design 'mul_f' '${irsid}' '${irsmode}' CLOCK '${ite}' '${orsid}' '${orsmode}' CLOCK '${ote}'"
        report_timing -nosplit -significant_digits 6 -capacitance -from [all_registers -clock_pins -clock ${iclk}] -to [all_registers -data_pins -clock ${oclk}] 
        puts "-- END Synthesis register_to_register:timing report for design 'mul_f' '${irsid}' '${irsmode}' CLOCK '${ite}' '${orsid}' '${orsmode}' CLOCK '${ote}'"
        }
    }
}
foreach { orsid orsmode oport ote } $o_candidates {
    foreach { irsid irsmode iclk ite } $clk_candidates {
        if { [llength [get_clocks -quiet ${iclk}] ] > 0 && [llength [all_registers -clock ${iclk}] ] > 0 } {
        puts "-- Synthesis register_to_output:timing report for design 'mul_f' '${irsid}' '${irsmode}' CLOCK '${ite}' '${orsid}' '${orsmode}' port '${ote}'"
        report_timing -nosplit -significant_digits 6 -capacitance -from [all_registers -clock_pins -clock ${iclk}] -to ${oport}
        puts "-- END Synthesis register_to_output:timing report for design 'mul_f' '${irsid}' '${irsmode}' CLOCK '${ite}' '${orsid}' '${orsmode}' port '${ote}'"
        }
    }
}
foreach { orsid orsmode oport ote } $o_candidates {
    foreach { irsid irsmode iport ite } $i_candidates {
        puts "-- Synthesis input_to_output:timing report for design 'mul_f' '${irsid}' '${irsmode}' port '${ite}' '${orsid}' '${orsmode}' port '${ote}'"
        report_timing -nosplit -significant_digits 6 -capacitance -from ${iport} -to ${oport}
        puts "-- END Synthesis input_to_output:timing report for design 'mul_f' '${irsid}' '${irsmode}' port '${ite}' '${orsid}' '${orsmode}' port '${ote}'"
    }
}
