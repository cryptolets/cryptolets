# Cryptolets

Cryptolets is a framework for generating and exploring cryptographic hardware. It builds from arithmetic primitives to modular operations, elliptic-curve point operations, and number theoretic transforms (NTTs). Each kernel can be configured, tested, and synthesized independently using Catapult HLS, with parallel sweeps for comparing hardware designs.

## Setup

- **Catapult HLS:** required to generate hardware. RTL verification uses QuestaSIM; downstream synthesis uses Design Compiler for ASICs or Vivado for FPGAs.
- **Tool and library paths:** copy [configs/config.example.sh](configs/config.example.sh) to `configs/config.local.sh`. Then set the paths for your machine.

```bash
./setup.sh
cp configs/config.example.sh configs/config.local.sh
```

Before you run commands, go to the repository root and activate the environment. Run all commands from the repository root.

```bash
source .venv/bin/activate
```



## Quick Start

Preview the modular addition sweep, then run it:

```bash
python3 run.py modadd --threads 16 --tp 1 --gen-only
python3 run.py modadd --threads 16 --tp 1
```

The first command is a dry run of sweep generation: it shows which configurations will run and saves them to `tmp_configs/modadd_configs.json` without launching Catapult. The second runs the sweep with a max of 16 designs in parallel, with 1 thread per design.

## Sweeping a Kernel

[run_config.yaml](configs/run_config.yaml) maps each kernel to a default sweep and a Catapult Tcl script. Edit the corresponding YAML in [default_sweeps_configs/](default_sweeps_configs/) to choose the designs to explore.

List-valued parameters define sweep choices. For example, the default bitshift sweep combines two widths and two shift directions on the Nangate 45nm library at 5 ns:

```yaml
BITWIDTH: [64, 128]
TECH_TYPE: [45nm]
TARGET_PERIOD: [5]  # ns
BITSHIFT_DIRECTION: [BITSHIFT_LEFT, BITSHIFT_RIGHT]
```

`SWEEP_ORDER` defines parameter expansion order. Preserve dependency ordering from the supplied configurations: [custom_sweep_overrides.py](utils/custom_sweep_overrides.py) adjusts curve widths, limb widths, and multiplier settings and filters unsupported or redundant combinations. The resulting sweep is therefore not always a simple Cartesian product.

Set `TEST` to check C++, `SIM` to verify RTL, and `SYN` to run downstream synthesis. For C++ testing only, enable both `TEST` and `TEST_ONLY`. `NUM_TEST_SAMPLES` controls the sample count. RTL generation still runs with `SYN: false` unless `TEST_ONLY` is enabled.

Use a specialized configuration by supplying both a sweep file and a core script:

```bash
python3 run.py ntt \
  --sweep-file custom_sweeps_configs/ntt_stockham_dit_sweep.yaml \
  --core-script tcl_cores/catapult_ntt_core.tcl \
  --gen-only
```


| Runner option       | Purpose                                                                |
| ------------------- | ---------------------------------------------------------------------- |
| `--threads`, `--tp` | Total thread budget and threads per Catapult process                   |
| `--sweep-file`      | Use this sweep YAML instead of the default; requires `--core-script`   |
| `--core-script`     | Use this Catapult Tcl script; requires `--sweep-file`                  |
| `--gen-only`        | Generate configuration JSON without launching jobs                     |
| `--run-only`        | Use an existing configuration JSON without regenerating it             |
| `--out-file`        | Override the default configuration JSON path                           |


Generated configurations go under `tmp_configs/`, batch logs under `logs/<kernel>/`, and Catapult projects and metric tables under `<level>/<kernel>/Catapult/`. Dry runs can still create configuration and log directories.

## Analyze Results

Pass the kernel's directory to [analyze.py](analyze.py):

```bash
python3 analyze.py lvl1_modops/modadd -t
python3 analyze.py lvl1_modops/modadd -c -o
```

The default selection is single-precision ASIC designs. Use `--fpga` for FPGAs and `--mp` for multi-precision designs.


| Option                              | Purpose                                                         |
| ----------------------------------- | --------------------------------------------------------------- |
| `-t`                                | Include technology names                                        |
| `-c`, `-o`                          | Export CSV and text tables to `results/csv/` and `results/txt/` |
| `--ccore`                           | Include reusable core solutions as well as the top-level design |
| `--curve`, `--bitwidth`, `--period` | Filter results                                                  |
| `--freq`                            | Display frequencies instead of clock periods                    |
| `--no-syn`                          | Exclude downstream synthesis metrics                            |
| `--find-optimal <CURVE>`            | Show Pareto-optimal, fastest, and smallest designs for a curve  |


Available metrics depend on which flow stages completed. The default cleaned table and Pareto comparison use `cycles × target_period` for latency. Rerun the command to inspect newly generated results; there is no built-in watch loop.

NTT also has [dedicated summaries and area-comparison plots](docs/ntt.md#demo-and-sweep-commands).

## Library of Kernels


| Level                                     | Kernels                                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| Level 0 — Primitives                      | `add_f`, `sub_f`, `cmul_f`, `bitshift`, `mul_f`, `sq_f`                                     |
| Level 1 — Modular arithmetic              | `modadd`, `modsub`, `modmul_mont`, `modmul_barrett`                                         |
| Level 2 — Point operations and transforms | `point_add`, `point_double`, `point_add_te`, `point_add_cyclonemsm`, `point_add_rcb`, `ntt` |


The [MTU scheduler](lvl2/mtu/Readme.md) is a standalone RTL component with its own simulation files.

## Documentation

More documentation is available in [docs/](docs/).

- [Extending the framework](docs/extending.md): adding a kernel using bitshift as a reference.
- [Point addition](docs/point-addition.md): adding curves and PADD formulas or coordinate systems.
- [NTT](docs/ntt.md): variants, demos, verification, and reporting.


## Usage Notes

- Parallel jobs require sufficient Catapult licenses, memory, and disk space.
- The first run that builds clusters for large (>512-bits) constant multipliers can take a few hours. For later runs, Catapult caches the clusters.
- FPGA multiplier choices and base widths affect DSP use differently across devices. Compare configurations on the actual target.
- The existing FPGA guidance recommends `CCORE_PERIOD_RATIO: [0.90]` for timing margin and provides custom libraries that bypass `mgc_add3`. These are target-specific tuning choices.
- The documented FPGA flow does not support `USE_CLUSTERS`, `FIXED_Q`, or `FIXED_CURVE_PARAMS`; use the supplied FPGA-compatible settings.
- The retained [point-operation reproduction script](scripts/reproduce_padd.sh) contains the larger experiment sweeps and defaults to configuration generation only.


## Contact

For questions or help using the framework, contact:

- Gaurav Kuwar, New York University — [gk2657@nyu.edu](mailto:gk2657@nyu.edu)
- Alhad Daftardar, New York University — [ajd9396@nyu.edu](mailto:ajd9396@nyu.edu)


## Citation

For the point-addition design-space study, see **Locus** and the [Locus branch](https://github.com/cryptolets/cryptolets/tree/locus).

If you use this framework in your research, please cite our [Locus paper](https://arxiv.org/abs/2609.18846):

```bibtex
@inproceedings{kuwar2026locus,
  author    = {Gaurav Kuwar and Alhad Daftardar and Jianqiao Mo and Siddharth Garg and Brandon Reagen},
  title     = {{Locus}: A Framework for Exploring and Optimizing Point Addition Hardware for Zero-Knowledge Proofs},
  booktitle = {Proceedings of the IEEE/ACM International Conference on Computer-Aided Design},
  year      = {2026},
  series    = {ICCAD '26},
  doi       = {10.1145/3831252.3834141},
  url       = {https://doi.org/10.1145/3831252.3834141}
}
```
