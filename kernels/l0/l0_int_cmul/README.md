# `l0_int_cmul` - Integer Constant Multiplication

## Description
Multiplication of an unsigned integer by a constant, $z = x \cdot c$, where $x$ is $W$ bits wide and $c$ is a $W_c$-bit constant fixed at design time. The full product is $W + W_c$ bits wide.

Because $c$ is known when the hardware is built, the HLS tool compiles the multiplier to shift-and-add: one shifted copy of $x$ per non-zero digit of $c$, summed in an adder tree. The zero digits of $c$ cost nothing, so a constant with a lower Hamming weight gives smaller and faster hardware. Catapult encodes $c$ in Non-Adjacent Form (NAF), a signed-digit form that minimizes the number of non-zero digits, so the area and latency follow the NAF weight, which is at most the binary weight.

A constant multiplier is much smaller and faster than a variable multiplier of the same width, since it has no partial-product array and its adder tree only has as many inputs as $c$ has non-zero digits. The drawback is that $c$ is hardwired: the hardware only computes products with that one constant, so a design built for one field or curve cannot be reused for another.

The output type selects which part of the product is kept: the full product, the low $W_c$ bits or the bits above $W$. A truncated output lets the HLS tool drop the logic that only fed the bits that were cut.

The constant is a template parameter generated into `params.h`. A parent kernel passes a field or curve constant: `l1_mod_mul` uses the reduction constants `q` and `q'` or `mu`, and `l1_mod_cmul` a curve coefficient `a`, `d` or `k`, converted to the Montgomery domain when Montgomery reduction is used. A kernel can also define custom constants under `structs` in its `kernel.yaml`. Standalone there is no field, so the sweep gives the constant's width, `cmul_const_w`, and Hamming weight, `cmul_hamming`, and the framework generates a seeded random constant from them. This sweeps the Hamming weight directly, to measure how the area and latency of a constant multiplier scale with it.

| port | direction | width |
|------|-----------|-------|
| `x`  | in        | `BITWIDTH` |
| `z`  | out       | `BITWIDTH + CMUL_CONST::W` (full), `CMUL_CONST::W` (lo) or `CMUL_CONST::W` (hi) |

Sweep design parameters:

- `bitwidth` — the width of `x`
- `cmul_const_w` — the width of the constant
- `cmul_hamming` — the fraction of the constant's bits that are set
- `cmul_output_type` — the part of the product kept: `cmul_output_full`, `cmul_output_lo` or `cmul_output_hi`
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs

## Test Sample Generation Strategy

The samples are the edge cases (`0`, `1`, the maximum and the midpoint) plus random operands. The random operands are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones. The golden output is the exact product of `x` and the generated constant, masked to the part selected by `cmul_output_type`, which is computed in the reference library.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l0_int_cmul -s sweeps/l0_int_cmul.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l0_int_cmul -s sweeps/l0_int_cmul.yaml --only syn
```

## Authors

Gaurav Kuwar
