#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/demo_env.sh"

python3 run.py ntt \
  --sweep-file custom_sweeps_configs/ntt_dif_korn_lambiotte_demo.yaml \
  --core-script tcl_cores/catapult_ntt_core.tcl \
  --gui \
  "$@"
