# `l1_mod_add` - Modular Addition

## Description
Addition in the prime field $\mathbb{F}_q$, $z = (a + b) \bmod q$, where $0 \le a, b < q$, $0 \le z < q$ and $q$ is the prime modulus.

| port | direction | width |
|------|-----------|-------|
| `a`  | in        | `FIELD::W` |
| `b`  | in        | `FIELD::W` |
| `q`  | in        | `FIELD::W` |
| `z`  | out       | `FIELD::W` |

Sweep design parameters:

- `bitwidth` — the width of the field elements; a named `field` sets it
- `field` — the prime field, for example `bn254_base`, or `arb_field` for a random prime of the bitwidth
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs
- `dep_period_ratio` — the clock period of a blackboxed child, as a ratio of `period`

## Dependencies

- `l0_int_add` with parameters `bitwidth = FIELD::W`
- `l0_int_sub` with parameters `bitwidth = FIELD::W + 1`

## Test Sample Generation Strategy

The samples are the edge cases (`0`, `q - 1` and the midpoint, in every pairing) plus random operand pairs. The random pairs are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones. Every operand is kept below the prime modulus `q`, so the samples are cryptographically sound. The golden output is `(a + b) mod q`, which is computed in the reference library.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l1_mod_add -s sweeps/l1_mod.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l1_mod_add -s sweeps/l1_mod.yaml --only syn
```

## Authors

Gaurav Kuwar
