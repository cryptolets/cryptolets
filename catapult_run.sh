#!/usr/bin/env bash
set -euo pipefail

DRY_RUN_ARG=""
GUI_ARG=""
ARGS=()

# Extract --dry-run and --gui from anywhere
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN_ARG="--dry-run"
    elif [[ "$arg" == "--gui" ]]; then
        GUI_ARG="--gui"
    else
        ARGS+=("$arg")
    fi
done

ALL_KERNELS=(
    # add_f 
    # sub_f 
    # cmul_f
    # modadd 
    # modsub
    # sq_f
    # modmul_mont
    # mul_f
    # modmul_barrett
    point_add 
    point_add_te
    # point_add_cyclonemsm
)

declare -A GROUP_MAP_PARAM=(
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
    [point_add_te]="padd_te"
    [point_add_cyclonemsm]="padd"
)

declare -A GROUP_MAP_CORE=(
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
    [point_add_te]="padd"
    [point_add_cyclonemsm]="padd"
)

usage() {
    echo "Usage: bash catapult_run.sh [--dry-run] [--gui] <kernel_name|all>"
    exit 1
}

if [ ${#ARGS[@]} -lt 1 ]; then
    usage
fi

if [ "${ARGS[0]}" = "all" ]; then
    kernels=("${ALL_KERNELS[@]}")
else
    kernels=("${ARGS[0]%/}")
fi

for kernel in "${kernels[@]}"; do
    group_name_core=${GROUP_MAP_CORE[$kernel]:-}
    group_name_param=${GROUP_MAP_PARAM[$kernel]:-}

    if [ -z "$group_name_core" ] || [ -z "$group_name_param" ]; then
        echo "Error: Unknown kernel '$kernel'" >&2
        usage
    fi

    CORE_CATAPULT_SCRIPT="catapult_${group_name_core}_core.tcl"
    PARAMS_TCL_SCRIPT="catapult_${group_name_param}_params.tcl"

    echo "=== Running Catapult for kernel=$kernel (script=$CORE_CATAPULT_SCRIPT) ==="
    bash run_catapult_parallel.sh $CORE_CATAPULT_SCRIPT $PARAMS_TCL_SCRIPT $kernel $DRY_RUN_ARG $GUI_ARG
done
