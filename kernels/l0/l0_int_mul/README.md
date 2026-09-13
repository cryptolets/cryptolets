# `l0_int_mul` - Integer Multiplication

## Description
Multiplication of unsigned integers, $z = x \cdot y$, with $W$-bit inputs and a $2W$-bit product. The output type selects which part of the product is kept: the full product, the low $W$ bits or the high $W$ bits. A truncated output lets the tools drop the logic that only fed the bits that were cut.

The multiplier is a recursive model with three layers, Karatsuba → schoolbook → native. Each layer splits the operands into smaller partial products until they reach a base width. `mul_type` selects the top layer, and the base widths select where each layer ends.

The two base widths are not swept directly. In the sweep file each is a map from `bitwidth` to a list of widths, and every design gets one entry from the list for its bitwidth:

```
base_mul_width:
  128: [64]
  254: [127, 63, 31, 15]
kar_base_mul_width:
  128: [64, 32]
  254: [127, 63, 31, 15]
```

A width the multiplier never splits down to is pinned to `bitwidth`: `mul_nor` pins both, `mul_sb` pins `kar_base_mul_width`. Combinations with `kar_base_mul_width` below `base_mul_width` are dropped, since Karatsuba would stop after schoolbook already took over.

| port | direction | width |
|------|-----------|-------|
| `x`  | in        | `BITWIDTH` |
| `y`  | in        | `BITWIDTH` |
| `z`  | out       | `2 * BITWIDTH` |

Sweep design parameters:

- `bitwidth` — the width of `x` and `y`
- `mul_type` — the multiplier structure: `mul_nor`, `mul_sb` or `mul_kar`
- `mul_output_type` — the part of the product kept: `mul_output_full`, `mul_output_lo` or `mul_output_hi`
- `base_mul_width` — the operand width at which the recursion stops and a native multiplier is used
- `kar_base_mul_width` — the operand width at which Karatsuba switches to schoolbook
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs

### Normal

`mul_nor` is the native multiplier of the HLS tool, `x * y`, with no decomposition. It is the baseline the other two structures are compared against.

### Schoolbook

`mul_sb` splits each operand into two halves, $x = x_1 2^h + x_0$ and $y = y_1 2^h + y_0$, and computes four partial products:

$$z = x_1 y_1 2^{2h} + (x_1 y_0 + x_0 y_1) 2^h + x_0 y_0$$

Each partial product is split again until both operands fit in `base_mul_width`, where the native multiplier takes over. The partial products are recombined with shifts and an adder tree.

### Karatsuba

`mul_kar` splits the operands the same way but computes only three products:

$$z_0 = x_0 y_0, \quad z_2 = x_1 y_1, \quad z_1 = (x_0 + x_1)(y_0 + y_1)$$

$$z = z_2 2^{2h} + (z_1 - z_0 - z_2) 2^h + z_0$$

One multiplication is traded for two additions and two subtractions. This lowers the area, but the additions lie on the critical path, so the latency is usually higher. Karatsuba is applied recursively until the operands fit in `kar_base_mul_width`, then schoolbook takes over down to `base_mul_width`, after which normal multipliers are used. The Karatsuba depth is set by the ratio of `bitwidth` to `kar_base_mul_width`.

## Test Sample Generation Strategy

The samples are the edge cases (`0`, the maximum and the midpoint, in every pairing) plus random operand pairs. The random pairs are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones. The golden output is the exact integer product, masked to the part selected by `mul_output_type`, which is computed in the reference library.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l0_int_mul -s sweeps/l0_int_mul.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l0_int_mul -s sweeps/l0_int_mul.yaml --only syn
```

## Authors

Gaurav Kuwar
