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
    # modmul_barrett
    # point_add 
    # point_add_cyclonemsm
)

# Map kernels to group name
declare -A GROUP_MAP=(
    [add_f]="lvl0"
    [sub_f]="lvl0"
    [cmul_f]="lvl0"
    [mul_f]="mul"
    [sq_f]="mul"

    [modadd]="lvl1"
    [modsub]="lvl1"
    [modmul_mont]="modmul"
    [modmul_barrett]="modmul"

    [point_add]="padd"
    [point_add_cyclonemsm]="padd"
)

# Usage
if [ $# -lt 1 ]; then
    echo "Usage: bash catapult_run.sh <kernel_name>"
    exit 1
fi

if [ "$1" = "all" ]; then
    kernels=("${ALL_KERNELS[@]}")
else
    kernels=(${1%/})
fi

for kernel in "${kernels[@]}"; do
    group_name=${GROUP_MAP[$kernel]:-}

    if [ -z "$group_name" ]; then
        echo "Error: Unknown kernel '$kernel'" >&2
        usage
    fi

    CORE_CATAPULT_SCRIPT="catapult_${group_name}_core.tcl"
    PARAMS_TCL_SCRIPT="catapult_${group_name}_params.tcl"

    echo "=== Running Catapult for kernel=$kernel (script=$CORE_CATAPULT_SCRIPT) ==="
    bash run_catapult_parallel.sh $CORE_CATAPULT_SCRIPT $PARAMS_TCL_SCRIPT $kernel
done
