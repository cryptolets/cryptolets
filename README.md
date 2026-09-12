![Tessera](imgs/mosaic.jpg)

# Tessera: A Framework for Cryptographic Hardware Kernels

Tessera is a fully automated design space exploration (DSE) framework for cryptographic hardware kernels, covering integer and modular arithmetic through elliptic curve point operations; kernels that dominate Zero-Knowledge Proofs (ZKPs) and Fully Homomorphic Encryption (FHE). A kernel is specified once in HLS C++, and a sweep as a set of parameter values. Each combination is built through high level synthesis (HLS), logic synthesis and power analysis. A single testbench verifies the design at the C++, RTL and gate level against a reference implementation of the arithmetic, and the resulting area, latency and power measurements are collected into one table. Together these define a highly productive methodology for hardware DSE of cryptographic kernels.

## Setup

### Tool versions

Tessera is tested against the following tool and dependency versions:

* `Catapult HLS Ultra` - 2026.1
* `Catapult QuestaSim` - 2026.2
* `Synposys Design Compiler` - Y-2026.03
* `Synposys PrimePower` - Y-2026.03
* `Vivado` - 2026.1
* `Python` - 3.9.25

### Initial Setup
```
bash setup.sh
source .venv/bin/activate    # activate.csh for tcsh

# Fill in config.yaml with the tool and library paths for your site.
cp config.yaml.tmpl config.yaml
```

## Quick Start

Build `l1_mod_add` at 64 and 128 bits to RTL. Catapult makes the RTL, and the testbench verifies the C++ and the RTL:

```
python -m tessera run l1_mod_add -s sweeps/quick_start_l1_mod_add.yaml --to rtl
```

Then you can use `analyze` to visualize metrics for the kernel:

```
python -m tessera analyze l1_mod_add
```

Synthesize that RTL with Design Compiler:

```
python -m tessera run l1_mod_add -s sweeps/quick_start_l1_mod_add.yaml --only syn
```

Run the testbench on the gate netlist from Design Compiler, then run power analysis:

```
python -m tessera run l1_mod_add -s sweeps/quick_start_l1_mod_add.yaml --from gls --to pwr
```

Generate RTL for a a 254-bit BN254 Montgomery modular multiplier.

```
python -m tessera run l1_mod_mul -s sweeps/quick_start_l1_mod_mul.yaml --to rtl
```

## How it works

A run starts from one *kernel* and one *sweep* file. The sweep lists values for each parameter, and Tessera crosses them into one *design* per combination. Tessera then resolves the dependencies of every design, recursively. A modular multiplier (`l1_mod_mul`) uses an integer multiplier (`l0_int_mul`) and a constant multiplier (`l0_int_cmul`). Each of those is its own kernel. Tessera derives the child designs a parent needs from the defined kernel implementation conventions, and through compiling and parsing of the parent design. A child designs are reused efficiently. Each child then goes through the full flow the parent needs. Overall, this process is designed to maximize design reuse, reduces runtime, and accelerates developer productivity.

### Designs and Dependency Scheduling Flow Diagram
<img src="imgs/design_dep_sch.png" alt="Designs and dependency scheduling" width="75%">

Per design, Tessera fully automates the end-to-end *flow*. The flow is a sequence of *steps*: code generation, C++ verification, HLS RTL generation, RTL simulation and verification, logic synthesis, gate-level simulation and verification, and activity-annotated power analysis. Each step runs a tool and records its metrics in the design's *package*. Tessera supports both ASIC and FPGA flows. For ASICs, OSCI does the C++ verification, Siemens Catapult HLS generates the RTL, Siemens QuestaSim runs the RTL and gate-level simulations, Synopsys Design Compiler performs the logic synthesis, and Synopsys PrimePower measures power from the recorded switching activity. FPGA synthesis is performed with Vivado.

### Per-Design Flow Diagram
![Per design flow](imgs/per_design_flow.png)

## Authors
Gaurav Kuwar

## References