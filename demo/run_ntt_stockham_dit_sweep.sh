#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/demo_env.sh"

python3 run.py ntt \
  --sweep-file custom_sweeps_configs/ntt_stockham_dit_sweep.yaml \
  --core-script tcl_cores/catapult_ntt_core.tcl \
  "$@"

python3 utils/summarize_ntt_tables.py \
  --configs tmp_configs/ntt_configs.json \
  --catapult-dir lvl2/ntt/Catapult
