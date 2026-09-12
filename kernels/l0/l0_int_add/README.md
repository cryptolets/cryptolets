# `l0_int_add` - Integer Addition

## Description

Unsigned integer addition, `z = x + y`.

| port | direction | width |
|------|-----------|-------|
| `x`  | in        | `BITWIDTH` |
| `y`  | in        | `BITWIDTH` |
| `z`  | out       | `BITWIDTH + 1` |

Sweep design parameters:

- `bitwidth` — the width of `x` and `y`
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs

## HLS RTL Generation and Simulation

Verifies the C+\\+, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l0_int_add -s sweeps/l0_int.yaml --to rtl
```

## Test Sample Generation Strategy

The samples are the edge cases (zero, the maximum and the midpoint, in every pairing) plus random operand pairs. The random pairs are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones. The golden output is the exact integer sum with carry included, which is computed in the reference library.

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l0_int_add -s sweeps/l0_int.yaml --only syn
```

## Authors

Gaurav Kuwar
