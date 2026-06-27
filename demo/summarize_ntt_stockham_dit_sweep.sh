#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/demo_env.sh"

python3 utils/summarize_ntt_tables.py \
  --configs tmp_configs/ntt_stockham_dit_configs.json \
  --catapult-dir lvl2/ntt/Catapult
