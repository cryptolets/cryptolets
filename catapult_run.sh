#!/usr/bin/env bash
set -euo pipefail

# List of all kernels to run in one go
ALL_KERNELS=(
  # add_f 
  # sub_f 
  # cmul_f
  # modadd 
  # modsub
  # mul_f
  # sq_f
  # modmul_mont 
  # point_add 
  # point_double 
  # padd_cyclonemsm
)

# Map kernels to group Tcl scripts
declare -A GROUP_MAP=(
    [add_f]="catapult_lvl0.tcl"
    [sub_f]="catapult_lvl0.tcl"
    [cmul_f]="catapult_lvl0.tcl"
    [mul_f]="catapult_mul.tcl"
    [sq_f]="catapult_mul.tcl"

    [modadd]="catapult_lvl1.tcl"
    [modsub]="catapult_lvl1.tcl"
    [modmul_mont]="catapult_modmul.tcl"
)

# Usage
if [ $# -lt 1 ]; then
    echo "Available kernels: ${ALL_KERNELS[*]}"
    exit 1
fi

if [ "$1" = "all" ]; then
    kernels=("${ALL_KERNELS[@]}")
else
    kernels=(${1%/})
fi

for kernel in "${kernels[@]}"; do
    script=${GROUP_MAP[$kernel]:-}

    if [ -z "$script" ]; then
        echo "Error: Unknown kernel '$kernel'" >&2
        usage
    fi

    echo "=== Running Catapult for kernel=$kernel (script=$script) ==="
    catapult -shell -eval "set kernel $kernel; source $script; exit"
done
