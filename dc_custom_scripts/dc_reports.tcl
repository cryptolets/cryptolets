set design [getenv "RTL_FILE"]

sh mkdir -p reports
sh mkdir -p netlist

write_file -hierarchy -format verilog -output "./netlist/${design}.v"
write_sdc "./netlist/${design}.sdc"

redirect ./reports/report_timing.rpt {
    source [file join [file dirname [info script]] get_timing_reports.tcl]
}

report_timing -delay max  -nosplit -input -nets -cap -max_path 10 -nworst 10    > ./reports/report_timing_max.rpt
report_timing -delay min  -nosplit -input -nets -cap -max_path 10 -nworst 10    > ./reports/report_timing_min.rpt
report_constraint -all_violators -verbose  -nosplit                             > ./reports/report_constraint.rpt
check_design -nosplit                                                           > ./reports/check_design.rpt
report_design                                                                   > ./reports/report_design.rpt
report_area                                                                     > ./reports/report_area.rpt
report_timing -loop                                                             > ./reports/timing_loop.rpt
report_power -hierarchy -analysis_effort high                                   > ./reports/report_power.rpt
report_qor                                                                      > ./reports/report_qor.rpt
report_area -hierarchy -nosplit                                                 > ./reports/report_area_hier.rpt
report_resources -hierarchy                                                     > ./reports/report_resources_hier.rpt