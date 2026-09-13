# `l2_point_add_sw` - Point Addition (Short Weierstrass)

## Description
Addition of two points on an elliptic curve. This kernel targets the Short Weierstrass form, $y^2 = x^3 + ax + b$. The points are in Jacobian coordinates $(X, Y, Z)$, which represent the affine point $(X/Z^2, Y/Z^3)$ and avoid the field inversion that affine addition needs. The formula is `add-2007-bl` from the Explicit-Formulas Database [1].

When both points are the same, point doubling is performed, which has a different formula. The doubling formula depends on the curve coefficient $a$ and is selected by `pdbl_form`, as described in the `l2_point_dbl_sw` README.


| port | direction | width |
|------|-----------|-------|
| `P0` | in        | `PointJac`, three `FIELD::W` coordinates |
| `P1` | in        | `PointJac`, three `FIELD::W` coordinates |
| `q`  | in        | `FIELD::W`, only with `var_q` |
| `rc` | in        | `FIELD::W` |
| `R`  | out       | `PointJac`, three `FIELD::W` coordinates |

Sweep design parameters:

- `bitwidth` — the width of the field elements; the `field` sets it
- `field` — the curve's base field, for example `bn254_base`
- `pdbl_form` — the doubling formula: `pdbl_a0`, `pdbl_a3` or `pdbl_avar`, matching the curve's $a$
- `mred` — the reduction algorithm: `mred_mont` or `mred_bar`
- `q_type` — `fixed_q` or `var_q`
- `rc_type` — `fixed_rc` or `var_rc`
- `mul_type` — the multiplier structure: `mul_nor`, `mul_sb` or `mul_kar`
- `base_mul_width` — the operand width at which the recursion stops and a native multiplier is used
- `kar_base_mul_width` — the operand width at which Karatsuba switches to schoolbook
- `period` — the target clock period, in ns
- `tech_type` — the target technology node or FPGA part
- `ii` — the initiation interval, the number of cycles between two accepted inputs
- `dep_period_ratio` — the clock period of a blackboxed child, as a ratio of `period`

## Dependencies

- `l1_mod_mul` — every product
- `l1_mod_cmul` — the product by $a$ in the `pdbl_avar` doubling
- `l1_mod_add`, `l1_mod_sub` — the sums and differences
- `l2_point_dbl_sw` — the doubling formulas for the equal-points case

## Test Sample Generation Strategy

Every sample is a pair of points that lie on the curve, so the kernel is only ever tested on valid group elements. The reference library generates each point by drawing a random $x$ in $\mathbb{F}_q$ and solving the curve equation for $y$, so the pair is a random point on the curve, not a random pair of field elements. In about 20% of the samples the second point equals the first, so the doubling branch is exercised as well as the addition branch. Pairs whose sum is the point at infinity are skipped, since the kernel does not represent it.

The golden output is the affine sum, which the reference library computes with the group law. The testbench converts the points from affine to Jacobian coordinates and the result back, and for Montgomery designs converts each coordinate into and out of the Montgomery domain.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l2_point_add_sw -s sweeps/l2_point_add_sw.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l2_point_add_sw -s sweeps/l2_point_add_sw.yaml --only syn
```

## Authors

Gaurav Kuwar

## References

[1] Daniel J. Bernstein and Tanja Lange. Explicit-Formulas Database. https://www.hyperelliptic.org/EFD
