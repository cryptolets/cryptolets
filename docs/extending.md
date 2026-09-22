# Extending the Framework

[Back to the README](../README.md)

Use the existing [bitshift kernel](../lvl0_primitives/bitshift/) as a small reference when adding a kernel. This guide follows the implementation currently in the repository. For new point-addition formulas, see the [PADD guide](point-addition.md).

## Adding a Kernel: Bitshift Example

Choose a kernel name and level, then copy the closest existing kernel's structure. The bitshift example consists of:

- `include/bitshift.h`: public function declaration.
- `src/bitshift.cpp`: synthesizable C++ implementation.
- `src/bitshift_tb.cpp`: C++/RTL verification testbench.
- `gen_samples.py`: input and expected-output generation.

## Source, Header, and Testbench

The bitshift function takes a `wide_t` operand and an integer shift amount. `BITSHIFT_DIRECTION` selects left or right shifting at compile time. Its header includes the shared [primitives.h](../utils/include/primitives.h), which defines `wide_t` using the generated `BITWIDTH` parameter.

For a new kernel, keep the header and function signature consistent with the top selected by Catapult. Adapt the testbench's input fields, function invocation, and output serialization to match. Reuse the CSV parsing and SCVerify conventions from the reference testbench.

## Sample and Golden-Output Generation

[bitshift/gen_samples.py](../lvl0_primitives/bitshift/gen_samples.py) accepts the width, sample count, output paths, and shift direction. It produces input and golden CSV files, including edge inputs and randomized samples.

Implement a software reference for the new operation and make its CSV columns agree with the C++ testbench. Model fixed-width behavior explicitly: bitshift's Python reference masks results to the configured width.

## Catapult Integration

Start with [catapult_bitshift_core.tcl](../tcl_cores/catapult_bitshift_core.tcl) or the closest existing flow. Update:

1. The level directory, source files, dependencies, and include paths.
2. `config_params`, read from the job's environment and used to generate `tmp_params.h`.
3. The top function, clock, and kernel-specific scheduling directives.
4. Sample-generator arguments and verification hooks.

Use [utils/util.tcl](../utils/util.tcl) for common setup, parameter generation, testing, RTL extraction, and downstream synthesis. Bitshift forwards `BITSHIFT_DIRECTION` through `run_osci_test`; parameters affecting a new reference model need equivalent argument plumbing.

## Sweep Parameters and Naming

Create a default sweep from [bitshift_sweep.yaml](../default_sweeps_configs/bitshift_sweep.yaml). Include each swept parameter in `SWEEP_ORDER`, along with the required control flags.

For symbolic parameters, add definitions to [params.h](../utils/include/params.h). Bitshift defines `BITSHIFT_LEFT` and `BITSHIFT_RIGHT` there. Add short keys, display keys, and symbolic-value mappings to [naming_config.yaml](../naming_config.yaml).

Add rules to [custom_sweep_overrides.py](../utils/custom_sweep_overrides.py) only when the new parameter needs dependent values or compatibility filtering.

## Kernel Registration and Reporting

Register the name in all three places in [run_config.yaml](../run_config.yaml):

- `KERNELS`.
- `SWEEP_GROUP_MAP`, which selects the default YAML.
- `CORE_GROUP_MAP`, which selects the Tcl script.

For example, bitshift maps to the `bitshift` group in both maps. Its new reporting field is explicitly included in `analyze.py` using the `bitshift_dir` display key; adding a naming entry alone does not create a report column.

Preview the new sweep before running it. Use `TEST: true` and `TEST_ONLY: true` for an initial C++ check, then enable RTL verification as appropriate. See [Sweeping a Kernel](../README.md#sweeping-a-kernel) for commands and execution flags.
