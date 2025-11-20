# Cryptolets
Framework for Cryptographic Hardware Modules

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

For running Modmul Montgomery and Barrett: 
```
python3 run.py modmul_mont --threads 8 --tp 2
python3 run.py modmul_barrett --threads 8 --tp 2
```

TODO:

## Monitor and Analyze Design Sweeps
Script to monitor sweep progress and get performance metrics.

```bash
python3 analyze.py <KERNEL_PATH> [--mp] [-a] [-o] [-c] [-t]
```

`--mp` - show only multi-precision designs, by default _anaylze_ shows single-precision design. \
`-a` - Show ASIC designs, by default _anaylze_ shows FPGA designs. \
`-c` and `-o` - Output metrics table to CSV and TXT files, respectively.
`-t` - Show technology node.

## Tips for running FPGA Sweeps
- Set `CCORE_PERIOD_RATIO = 0.90`, allows for ccore's to meet parent module's timing in FGPA.
- Use custom modified library (remove `mgc_add3`) to bypass it bottlenecking high clock speeds.
- `USE_CLUSTERS`
- For certain FPGAs (e.g. VU9P) depending on type of DSP using lower _Base Multiplier Width_ and Lowering _Karatsuba Multiplier Width_ can achieve lower DSP usage, the opposite is true for other FPGAs (e.g VH1782, VH1582, etc.)