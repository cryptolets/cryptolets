set max_cores [getenv "THREADS_PER_PROCESS"]

set_host_options -max_cores $max_cores
puts "setting max cores to $max_cores"