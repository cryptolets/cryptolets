set sfd [file dirname [info script]]
set root_dir [file normalize [file join [file dirname [info script]] .. ..]]
source [file join $root_dir cryptolets tcl util.tcl] ;# Import utilities

init_options

project new
options set Farm/EnableRemoteConstraintSweep false
options set Farm/Workers $::env(THREADS)

solution file add [file join $sfd $::env(SWEEP_YAML)]
go extract