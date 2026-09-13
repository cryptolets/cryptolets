# `l0_int_sq` - Integer Squaring

## Description
Squaring of an unsigned integer, $z = x^2$, with a $W$-bit input and a $2W$-bit product. Squaring is a multiplication with equal operands, so the symmetric partial products appear twice and are computed once, which reduces the partial products without the extra additions of Karatsuba.

The multiplier structures, the base widths and how the sweep file maps `bitwidth` to them are described in the `l0_int_mul` README. Squaring adds one layer on top: with `mul_kar`, the input is split into halves, $x = x_1 2^h + x_0$, and the square is

$$z = x_1^2 2^{2h} + 2 x_0 x_1 2^h + x_0^2$$

The two squares recurse into this kernel until the operands fit in `kar_base_mul_width`, and the cross product $x_0 x_1$ is a `l0_int_mul` Karatsuba multiplier. The factor of 2 is a shift. With `mul_sb` and `mul_nor` the square is a `l0_int_mul` schoolbook or normal multiplier with both operands set to `x`.

| port | direction | width |
|------|-----------|-------|
| `x`  | in        | `BITWIDTH` |
| `z`  | out       | `2 * BITWIDTH` |

Sweep design parameters:

- `bitwidth` — the width of `x`
- `mul_type` — the multiplier structure: `mul_nor`, `mul_sb` or `mul_kar`
- `base_mul_width` — the operand width at which the recursion stops and a native multiplier is used
- `kar_base_mul_width` — the operand width at which Karatsuba switches to schoolbook
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs

## Test Sample Generation Strategy

The samples are the edge cases (`0`, `1`, the maximum and the midpoint) plus random operands. The random operands are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones. The golden output is the exact integer square, which is computed in the reference library.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l0_int_sq -s sweeps/l0_int_mul.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l0_int_sq -s sweeps/l0_int_mul.yaml --only syn
```

## Authors

Gaurav Kuwar
