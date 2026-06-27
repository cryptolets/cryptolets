#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/demo_env.sh"

CONFIG_JSON="tmp_configs/ntt_kl_dif_demo_configs.json"

python3 run.py ntt \
  --sweep-file custom_sweeps_configs/ntt_dif_korn_lambiotte_demo.yaml \
  --core-script tcl_cores/catapult_ntt_core.tcl \
  --out-file "${CONFIG_JSON}" \
  --gui \
  "$@"
