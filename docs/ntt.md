# NTT Implementation Flow

The [NTT directory](../lvl2/ntt/) contains the C++ Catapult NTT implementation and the Python software models used to generate test vectors and validate algorithm variants.

## Implemented NTT Families

- Standard Cooley-Tukey variants:
  - `NTT_STANDARD_DIF_NR`
  - `NTT_STANDARD_DIF_RN`
  - `NTT_STANDARD_DIT_NR`
  - `NTT_STANDARD_DIT_RN`
- Constant-geometry variants:
  - `NTT_PEASE_DIF`
  - `NTT_PEASE_DIT`
  - `NTT_KORN_LAMBIOTTE_DIF`
  - `NTT_KORN_LAMBIOTTE_DIT`
- Stockham variants:
  - `NTT_STOCKHAM_DIF`
  - `NTT_STOCKHAM_DIT`

`NTT_IMPL` selects the family:

- `NTT_IMPL_STANDARD`
- `NTT_IMPL_CONSTANT_GEOMETRY`
- `NTT_IMPL_STOCKHAM`

The family-specific variant variable selects the butterfly schedule:

- `NTT_STANDARD_VARIANT`
- `NTT_CONSTANT_GEOMETRY_VARIANT`
- `NTT_STOCKHAM_VARIANT`

## Demo And Sweep Commands

Run these commands from the repository root.

Korn-Lambiotte DIF GUI demo:

```bash
./scripts/ntt_demo/run_ntt_kl_dif_demo.sh
```

Korn-Lambiotte DIF sweep:

```bash
./scripts/ntt_demo/run_ntt_kl_dif_sweep.sh
```

This also prints a summary of the generated Catapult tables, latency cycles, and area.

Stockham DIT GUI demo:

```bash
./scripts/ntt_demo/run_ntt_stockham_dit_demo.sh
```

Stockham DIT sweep:

```bash
./scripts/ntt_demo/run_ntt_stockham_dit_sweep.sh
```

This also prints a summary of the generated Catapult tables, latency cycles, and area.

Summaries for the most recent sweeps:

```bash
./scripts/ntt_demo/summarize_ntt_kl_dif_sweep.sh
./scripts/ntt_demo/summarize_ntt_stockham_dit_sweep.sh
```

KL-DIF versus Stockham DIT normalized area comparison:

```bash
./scripts/ntt_demo/plot_ntt_kl_vs_stockham_dit_area_compare.sh
```

This writes:

```text
lvl2/ntt/plots/ntt_kl_vs_stockham_dit_area_compare.csv
lvl2/ntt/plots/ntt_kl_vs_stockham_dit_area_compare.png
```

The comparison plotter uses Matplotlib and groups Catapult RTL area into `Control Logic`, `Datapath`, `Reg`, and `Memory`. The wrapper uses `.venv/bin/python` when that environment exists.

Add `--dry-run` to the `run_ntt_*` scripts to print the generated Catapult command without launching Catapult. Sweep wrappers still print their summaries afterward. The summary and plotting scripts do not support this option.

## File List For Commit

Python NTT software models and sample generation:

```text
lvl2/ntt/gen_samples.py
lvl2/ntt/common/__init__.py
lvl2/ntt/common/utils.py
lvl2/ntt/common/standard.py
lvl2/ntt/common/constant_geometry.py
lvl2/ntt/common/stockham.py
```

C++ NTT implementation and headers:

```text
lvl2/ntt/include/ntt.h
lvl2/ntt/include/ntt_common.h
lvl2/ntt/include/ntt_standard.h
lvl2/ntt/include/ntt_constant_geometry.h
lvl2/ntt/include/ntt_stockham.h
lvl2/ntt/src/ntt.cpp
lvl2/ntt/src/ntt_common.cpp
lvl2/ntt/src/ntt_standard.cpp
lvl2/ntt/src/ntt_constant_geometry.cpp
lvl2/ntt/src/ntt_stockham.cpp
lvl2/ntt/src/ntt_tb.cpp
```

Catapult, parameter, and naming support:

```text
utils/include/params.h
utils/util.tcl
tcl_cores/catapult_ntt_core.tcl
naming_config.yaml
run_config.yaml
run_catapult_parallel.sh
default_sweeps_configs/ntt_sweep.yaml
```

Korn-Lambiotte DIF demo and sweep:

```text
custom_sweeps_configs/ntt_dif_korn_lambiotte_demo.yaml
custom_sweeps_configs/ntt_dif_korn_lambiotte_sweep.yaml
scripts/ntt_demo/demo_env.sh
scripts/ntt_demo/run_ntt_kl_dif_demo.sh
scripts/ntt_demo/run_ntt_kl_dif_sweep.sh
scripts/ntt_demo/summarize_ntt_kl_dif_sweep.sh
scripts/ntt_demo/summarize_ntt_stockham_dit_sweep.sh
scripts/ntt_demo/plot_ntt_kl_vs_stockham_dit_area_compare.sh
utils/summarize_ntt_tables.py
utils/plot_ntt_area_compare.py
```

Stockham DIT demo and sweep:

```text
custom_sweeps_configs/ntt_stockham_dit_demo.yaml
custom_sweeps_configs/ntt_stockham_dit_sweep.yaml
scripts/ntt_demo/run_ntt_stockham_dit_demo.sh
scripts/ntt_demo/run_ntt_stockham_dit_sweep.sh
```

Documentation:

```text
lvl2/ntt/README.md
docs/ntt.md
```

## Files To Avoid Committing

Do not commit generated Catapult projects, generated CSVs, caches, or temporary debug traces:

```text
lvl2/ntt/Catapult/
lvl2/ntt/__pycache__/
lvl2/ntt/common/__pycache__/
lvl2/ntt/samples/
lvl2/ntt/goldens/
lvl2/ntt/*_twiddle*.txt
lvl2/ntt/*_twiddle_debug.txt
```
