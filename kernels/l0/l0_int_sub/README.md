# `l0_int_sub` - Integer Subtraction

## Description

Subtraction of unsigned integers, `z = x - y`, with a signed result. In the cryptographic context the inputs are field residues or integers that are never negative, so unsigned inputs avoid a wasted sign bit. The result is one bit wider and signed: the extra bit is the borrow out of the subtraction, so the sign costs no extra hardware.

| port | direction | width |
|------|-----------|-------|
| `x`  | in        | `BITWIDTH` |
| `y`  | in        | `BITWIDTH` |
| `z`  | out       | `BITWIDTH + 1`, signed |

Sweep design parameters:

- `bitwidth` — the width of `x` and `y`
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs

## HLS RTL Generation and Simulation

Verifies the C+\\+, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l0_int_sub -s sweeps/l0_int.yaml --to rtl
```

## Test Sample Generation Strategy

The samples are the edge cases (zero, the maximum and the midpoint, in every pairing) plus random operand pairs. The random pairs are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones, and about half of the differences are negative. The golden output is the exact signed integer difference, which is computed in the reference library.

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l0_int_sub -s sweeps/l0_int.yaml --only syn
```

## Authors

Gaurav Kuwar
