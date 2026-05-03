source [file join $::env(ROOT_DIR) cryptolets tcl util.tcl] ;# Import utilities

init_options

project new
options set Farm/EnableRemoteConstraintSweep false
options set Farm/Workers $::env(THREADS)

solution file add $::env(SWEEP_YAML)
go extract