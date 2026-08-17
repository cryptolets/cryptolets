![Tessera](imgs/mosaic.jpg)

# Tessera: A Framework for Cryptographic Hardware Kernels

Tessera is a framework for design space exploration over a library of
cryptographic kernels, from integer and modular arithmetic to elliptic curve
point operations. You write a kernel once in C++. Tessera builds every point in
a sweep through high level synthesis, logic synthesis, gate level simulation and
power analysis, then collects what each design measured into one table.

Tessera is under the Cryptolets project.

## Setup

### Tool versions

Tessera is tested against the following tool and dependency versions:

* `catapult` - 2026.1
* `questasim` - 2026.2
* `design compiler` - Y-2026.03
* `primetime` - Y-2026.03
* `vivado` - 2026.1
* `python` - 3.9.25

### Intial Setup
```
bash setup.sh

# Fillout `config.yaml` with your tool paths.
cp config.yaml.tmp config.yaml
```

## Quick start

```
.venv/bin/python -m tessera run l1_mod_add -s sweeps/l1_mod.yaml
.venv/bin/python -m tessera analyze l1_mod_add
```

- The first command also builds `l0_int_add` and `l0_int_sub`, because `l1_mod_add` blackboxes them
- `-t` sets the thread count
- `--dry-run` writes the files a tool would read, then stops
- `--dc-only` synthesizes an existing Catapult build again
- `--run-only` reuses the design list from the last run

## The Flow

<!-- Some Diagram here -->

### ASIC

```
Catapult -> package -> Design Compiler -> gate level simulation -> PrimeTime
```

- **Catapult** — C++ to RTL, and writes the package the parents read
- **Design Compiler** — RTL to a gate netlist, and estimates power
- **gate level simulation** — runs the RTL testbench against that netlist, and records switching activity
- **PrimeTime** — measures power from that activity

### FPGA

- Vivado runs inside the Catapult run, so no stages follow it
- A `tech_type` that starts with `fpga` takes this flow
- Reports LUTs, FFs, DSPs and BRAMs instead of area
- _Note: Blackboxing is not supported here yet, so every dep is inlined_

## Concepts

### Kernels and designs

- **kernel** — one operation, such as `l1_mod_add`, in `kernels/<level>/<name>/`
- **design** — one point in a sweep, such as that kernel at bitwidth 32, period 1.0
- **sweep** — the parameters to build, and the flags that say how far to take them
- Levels: `l0` integer, `l1` modular, `l2` point, `l3` higher operations

### Packaging Kernels

- **package** — a built design's RTL and its manifest, which records ports, area, delay, latency and power
- **blackbox** — a parent reuses a dep's package instead of compiling the dep again
- Blackboxing keeps a large design inside what synthesis can handle
- A dep the kernel does not blackbox is inlined, and needs no build of its own
- Tessera builds the blackboxed deps itself, at the width and period the parent needs

## Writing a sweep

### Parameters

- Every list is crossed with the others, so 2 bitwidths and 3 periods build 6 designs
- `bitwidth`, `tech_type`, `period`, `ii`
- `curve`, `field`, `q_type`
- `dep_period_ratio` — a blackboxed dep is built at `period * ratio`

### Flags

- A flag turns on the stages it needs: `power` → `gls` → `syn` and `verify_rtl` → `test_cpp`
- `syn_sel` picks which designs are worth synthesizing:
  - `all` — every design
  - `pareto` — the designs on the area and latency frontier
  - `small_fast` — the smallest and the fastest of those
- Only designs that compute the same thing are compared, which `kernel_key` decides

## Adding a New Kernel

```
.venv/bin/python -m tessera new <kernel>
```

### The implementation

- `kernels/<level>/<name>/impl/<name>_impl.h`
- The class Tessera reads for its ports and its deps
- Template parameters take the design's values, such as `_FIELD::W`

### kernel.yaml

- `deps` — the kernels this one uses
- `blackbox` — which of those to reuse as packaged RTL
- `kernel_key` — the parameters that decide what the kernel computes, so two designs are only compared when one could replace the other
- `stages` — extra TCL per Catapult stage

### The testbench

- `kernels/<level>/<name>/<name>_tb.cpp` drives `CCS_DESIGN`
- `gen_samples.py` writes the samples and the golden outputs
- The same testbench checks the C++, the RTL and the gate netlist

## Authors
Gaurav Kuwar

## References