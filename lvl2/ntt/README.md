# NTT Implementation Flow

This directory contains the C++ Catapult NTT implementation and the Python software models used to generate test vectors and validate algorithm variants.

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

Korn-Lambiotte DIF GUI demo:

```bash
./demo/run_ntt_kl_dif_demo.sh
```

Korn-Lambiotte DIF sweep:

```bash
./demo/run_ntt_kl_dif_sweep.sh
```

This also writes:

```text
lvl2/ntt/Catapult/ntt_kl_dif_area_breakdown.csv
lvl2/ntt/Catapult/ntt_kl_dif_area_breakdown.png
```

Stockham DIT GUI demo:

```bash
./demo/run_ntt_stockham_dit_demo.sh
```

Stockham DIT sweep:

```bash
./demo/run_ntt_stockham_dit_sweep.sh
```

This also writes:

```text
lvl2/ntt/Catapult/ntt_stockham_dit_area_breakdown.csv
lvl2/ntt/Catapult/ntt_stockham_dit_area_breakdown.png
```

Area breakdown plot for the most recent sweep:

```bash
./demo/summarize_ntt_kl_dif_sweep.sh
./demo/plot_ntt_kl_dif_area_breakdown.sh
./demo/summarize_ntt_stockham_dit_sweep.sh
./demo/plot_ntt_stockham_dit_area_breakdown.sh
```

The plotter groups Catapult RTL area into `Control Logic`, `Datapath`, `Reg`, and `Memory`.
`Memory` is omitted when it is zero for every design in the selected sweep.
The sweep scripts write the area chart as PNG; pass `--out-svg` to `utils/plot_ntt_area_breakdown.py` only if a retained SVG is needed.

KL-DIF versus Stockham DIT normalized area comparison:

```bash
./demo/plot_ntt_kl_vs_stockham_dit_area_compare.sh
```

This writes:

```text
lvl2/ntt/plots/ntt_kl_vs_stockham_dit_area_compare.csv
lvl2/ntt/plots/ntt_kl_vs_stockham_dit_area_compare.png
```

The comparison plotter uses Matplotlib. The wrapper uses `.venv/bin/python` when that environment exists.

Add `--dry-run` to any of these scripts to print the generated Catapult command without running synthesis.

## File List For Commit

Python NTT software models and sample generation:

```text
lvl2/ntt/gen_samples.py
lvl2/ntt/ntt_sw_utils.py
lvl2/ntt/ntt_standard_sw_models.py
lvl2/ntt/ntt_constant_geometry_sw_models.py
lvl2/ntt/ntt_stockham_models.py
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
requirements.txt
```

Korn-Lambiotte DIF demo and sweep:

```text
custom_sweeps_configs/ntt_dif_korn_lambiotte_demo.yaml
custom_sweeps_configs/ntt_dif_korn_lambiotte_sweep.yaml
demo/demo_env.sh
demo/run_ntt_kl_dif_demo.sh
demo/run_ntt_kl_dif_sweep.sh
demo/plot_ntt_area_breakdown.sh
demo/summarize_ntt_kl_dif_sweep.sh
demo/plot_ntt_kl_dif_area_breakdown.sh
demo/summarize_ntt_stockham_dit_sweep.sh
demo/plot_ntt_stockham_dit_area_breakdown.sh
demo/plot_ntt_kl_vs_stockham_dit_area_compare.sh
utils/summarize_ntt_tables.py
utils/plot_ntt_area_breakdown.py
utils/plot_ntt_area_compare.py
utils/plot_ntt_area_compare_svg_legacy.py
```

Stockham DIT demo and sweep:

```text
custom_sweeps_configs/ntt_stockham_dit_demo.yaml
custom_sweeps_configs/ntt_stockham_dit_sweep.yaml
demo/run_ntt_stockham_dit_demo.sh
demo/run_ntt_stockham_dit_sweep.sh
```

This README:

```text
lvl2/ntt/README.md
```

## Files To Avoid Committing

Do not commit generated Catapult projects, generated CSVs, caches, or temporary debug traces:

```text
lvl2/ntt/Catapult/
lvl2/ntt/__pycache__/
lvl2/ntt/samples/
lvl2/ntt/goldens/
lvl2/ntt/*_twiddle*.txt
lvl2/ntt/*_twiddle_debug.txt
```

`lvl2/ntt/ntt_dif_nr_only.py` is intentionally not part of the commit list.
