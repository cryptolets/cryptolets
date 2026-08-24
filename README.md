# Locus - A Framework for Exploring and Optimizing Point Addition Hardware for Zero-Knowledge Proofs

_Locus_ enables Design Space Exploration (DSE) and sweep generation for optimized point addition, modular multiplication (modmul), and all other hardware units in isolation. Quickly run large sweeps over a number of design parameters in parallel.

## Setup
```
./setup.sh
```
_Note: Might need to setup paths to Catapult lib and Design Compiler db files._

## General Usage
```
python3 run.py <KERNEL_NAME> [--threads <TOTAL_THREADS>] [--tp <THREADS_PER_PROCESS>] [--gen-only]
```
`--gen-only` - will only generate the sweep list without running Catapult.

### Examples
The first will generate a sweep from the `default_sweeps_configs/lvl1_sweep.yaml` file (good to check what will run), then we can perform the actual sweep:
```
python3 run.py modadd --threads 16 --tp 4 --gen-only
python3 run.py modadd --threads 16 --tp 4
```

For running __Modmul Montgomery__ and __Barrett__: 
```
python3 run.py modmul_mont --threads 8 --tp 2
python3 run.py modmul_barrett --threads 8 --tp 2
```

For running __Point Addition__: Short Weierstrass Addition, Doubling, Twisted Edwards Unified Addition, and CycloneMSM implementation: 
```
python3 run.py point_add --threads 16 --tp 4
python3 run.py point_double --threads 16 --tp 4
python3 run.py point_double_te --threads 16 --tp 4
python3 run.py point_add_cyclonemsm --threads 16 --tp 4
```

## Monitor and Analyze Design Sweeps
Script to monitor sweep progress and get performance metrics.

```bash
python3 analyze.py <KERNEL_PATH> [--mp] [-a] [-o] [-c] [-t] [--find-optimal <CURVE>]
```

`--mp` - show only multi-precision designs, by default _anaylze_ shows single-precision design. \
`-a` - Show ASIC designs, by default _anaylze_ shows FPGA designs. \
`-c` and `-o` - Output metrics table to CSV and TXT files, respectively. \
`-t` - Show technology node. \
`--find-optimal` - Additionally, returns pareto optimal, fastest, and smallest designs.

## Reproduce Full Sweep
```
./reproduce.sh
```

## Tips for running FPGA Sweeps
- Set `CCORE_PERIOD_RATIO = 0.90`, allows for ccore's to meet parent module's timing in FGPA.
- Use custom modified library (remove `mgc_add3`) to bypass it bottlenecking high clock speeds.
- For certain FPGAs (e.g. VU9P) depending on type of DSP using lower _Base Multiplier Width_ and Lowering _Karatsuba Multiplier Width_ can achieve lower DSP usage, the opposite is true for other FPGAs (e.g VH1782, VH1582, etc.)
- Not Supported on FPGA: `USE_CLUSTERS`, `FIXED_Q` and `FIXED_CURVE_PARAMS`

## Running Sweeps in Parallel 
1. **License limits**: Ensure you have enough Catapult licenses for as number of parallel runs.
2. **Memory usage**: Monitor system memory with many parallel processes
3. **Disk I/O**: Each process creates substantial temporary files