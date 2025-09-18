set max_cores [getenv "DESIGN_COMPILER_THREADS"]

set_host_options -max_cores $max_cores
puts "setting max cores to $max_cores"