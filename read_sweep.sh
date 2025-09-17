#!/bin/bash

source utils/parallel_helpers.sh

load_tcl_sweep_params params_lvl0.tcl

echo "Defined sweep all: ${SWEEPS_ALL[@]}"
echo "Defined sweep set: ${SWEEPS_PROJ_ORDER[@]}"
echo

print_config() {
  local line="Combination:"
  for k in "${SWEEPS_PROJ_ORDER[@]}"; do
    line+=" $k=${SWEEP_STATE[$k]}"
  done
  echo "$line"
}

sweep_recurse 0 print_config

# # Use arrays
# for target_ii in "${target_iis[@]}"; do
#     for bitwidth in "${bitwidths[@]}"; do
#         for target_period in "${target_periods[@]}"; do
#             echo "Launching run II=$target_ii BW=$bitwidth TP=$target_period"
#         done
#     done
# done