#!/usr/bin/env bash

# Global toggles
DRY_RUN=""               # "--dry-run" to enable
GEN_ONLY=""    # "--gen-only" to enable

# Compose flags safely
FLAGS=()
[[ -n "${DRY_RUN}" ]] && FLAGS+=(--dry-run)
[[ -n "${GEN_ONLY}" ]] && FLAGS+=(--gen-only)

CORE="tcl_cores/catapult_padd_core.tcl"


python3 run.py point_add_te --threads 40 --tp 1 \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_te_sweep_sp_nor.yaml "${FLAGS[@]}" > run_padd_te_sp_nor.log

python3 run.py point_add_te --threads 40 --tp 1 \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_te_sweep_sp.yaml "${FLAGS[@]}" > run_padd_te_sp.log

# python3 run.py point_add_te --threads 40 --tp 1 \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_te_sweep_mp.yaml "${FLAGS[@]}" > run_padd_te_mp.log


python3 run.py point_add --threads 40 --tp 1 \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_sw_sweep_sp_nor.yaml "${FLAGS[@]}" > run_padd_sw_sp_nor.log

python3 run.py point_add --threads 40 --tp 1 \
  --core-script "${CORE}" \
  --sweep-file full_sweeps_configs/padd_sw_sweep_sp.yaml "${FLAGS[@]}" > run_padd_sw_sp.log

# python3 run.py point_add --threads 40 --tp 1 \
#   --core-script "${CORE}" \
#   --sweep-file full_sweeps_configs/padd_sw_sweep_mp.yaml "${FLAGS[@]}" > run_padd_sw_mp.log
