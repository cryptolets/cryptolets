#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/demo_env.sh"

CONFIG_JSON="tmp_configs/ntt_stockham_dit_configs.json"
AREA_CSV="lvl2/ntt/Catapult/ntt_stockham_dit_area_breakdown.csv"
AREA_PNG="lvl2/ntt/Catapult/ntt_stockham_dit_area_breakdown.png"

python3 run.py ntt \
  --sweep-file custom_sweeps_configs/ntt_stockham_dit_sweep.yaml \
  --core-script tcl_cores/catapult_ntt_core.tcl \
  --out-file "${CONFIG_JSON}" \
  "$@"

python3 utils/summarize_ntt_tables.py \
  --configs "${CONFIG_JSON}" \
  --catapult-dir lvl2/ntt/Catapult

