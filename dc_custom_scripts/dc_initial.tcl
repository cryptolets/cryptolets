set max_cores [getenv "THREADS_PER_PROCESS"]

set_host_options -max_cores $max_cores
puts "setting max cores to $max_cores"

# Suppress messages, stopping log file size from exploding
set_svf -off
suppress_message FMLINK-1
suppress_message UID-401
suppress_message TIM-164