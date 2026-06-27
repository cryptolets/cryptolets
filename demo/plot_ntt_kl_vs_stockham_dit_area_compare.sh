#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/demo_env.sh"

if [[ -x .venv/bin/python ]]; then
  PYTHON=.venv/bin/python
else
  PYTHON=python3
fi

export MPLCONFIGDIR="${TMPDIR:-/tmp}/cryptolets-matplotlib-${USER:-user}"
mkdir -p "${MPLCONFIGDIR}"
SYSTEM_SITE_PACKAGES="$(python3 - <<'PY'
import site
print(":".join(site.getsitepackages()))
PY
)"
export PYTHONPATH="${SYSTEM_SITE_PACKAGES}:${PYTHONPATH:-}"

"${PYTHON}" utils/plot_ntt_area_compare.py \
  --baseline-configs tmp_configs/ntt_kl_dif_configs.json \
  --compare-configs tmp_configs/ntt_stockham_dit_configs.json \
  --catapult-dir lvl2/ntt/Catapult \
  --baseline-label KL-DIF \
  --compare-label ST-DIT \
  --out-csv lvl2/ntt/Catapult/ntt_kl_vs_stockham_dit_area_compare.csv \
  --out-png lvl2/ntt/Catapult/ntt_kl_vs_stockham_dit_area_compare.png
