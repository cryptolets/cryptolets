# `l1_mod_cmul` - Modular Constant Multiplication

## Description
Multiplication in the prime field $\mathbb{F}_q$ by a constant, $z = x \cdot c \bmod q$, where $0 \le x < q$, $0 \le z < q$ and $c$ is a field or curve constant fixed at design time. The kernel is a `l1_mod_mul` with one operand baked into the hardware: the product $t = x \cdot c$ is a `l0_int_cmul`, and the reduction, the reduction constant `rc` and the fixed or variable $q$ and `rc` are the same as in the `l1_mod_mul` README.

The constant is named in the sweep as a field member, for example `bn254_base-b` for the curve coefficient $b$. With Montgomery reduction the constant must already be in the Montgomery domain, so the `_mont` member is used, for example `bn254_base-b_mont`.

| port | direction | width |
|------|-----------|-------|
| `x`  | in        | `FIELD::W` |
| `q`  | in        | `FIELD::W`, only with `var_q` |
| `rc` | in        | `FIELD::W` |
| `z`  | out       | `FIELD::W` |

Sweep design parameters:

- `bitwidth` — the width of the field elements; a named `field` sets it
- `field` — the prime field: a curve's base field, for example `bn254_base`, its scalar field, `bn254_scalar`, or `arb_field` for a random prime of the bitwidth
- `cmul_const` — the constant, as `field-member`
- `mred` — the reduction algorithm: `mred_mont` or `mred_bar`
- `q_type` — `fixed_q` or `var_q`
- `rc_type` — `fixed_rc` or `var_rc`
- `mul_type` — the multiplier structure of the reduction's variable multiplies: `mul_nor`, `mul_sb` or `mul_kar`
- `base_mul_width` — the operand width at which the recursion stops and a native multiplier is used
- `kar_base_mul_width` — the operand width at which Karatsuba switches to schoolbook
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs
- `dep_period_ratio` — the clock period of a blackboxed child, as a ratio of `period`

## Dependencies

- `l0_int_cmul` with parameters `bitwidth = FIELD::W` — the product $x \cdot c$, and the products by $q$ and `rc` when fixed
- `l0_int_mul` with parameters `bitwidth = FIELD::W` — the products by $q$ and `rc` when variable
- `l1_mod_mul` — the Montgomery and Barrett reductions are implemented in that kernel, so this kernel depends on it even though it does not instantiate a full modular multiplier

## Test Sample Generation Strategy

The samples are the edge cases (`0`, `q - 1` and the midpoint) plus random operands. The random operands are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones. Every operand is kept below the prime modulus `q`, so the samples are cryptographically sound. The golden output is $x \cdot c \bmod q$ on plain operands, which is computed in the reference library. For Montgomery designs the testbench converts the operands into and out of the Montgomery domain.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l1_mod_cmul -s sweeps/l1_mod_cmul.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l1_mod_cmul -s sweeps/l1_mod_cmul.yaml --only syn
```

## Authors

Gaurav Kuwar