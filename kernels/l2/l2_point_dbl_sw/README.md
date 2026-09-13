# `l2_point_dbl_sw` - Point Doubling (Short Weierstrass)

## Description
Doubling of a point on an elliptic curve, $R = 2P$. This kernel targets the Short Weierstrass form, $y^2 = x^3 + ax + b$. The point is in Jacobian coordinates $(X, Y, Z)$, which represent the affine point $(X/Z^2, Y/Z^3)$ and avoid the field inversion that affine doubling needs. The formula depends on the curve coefficient $a$: curves with $a = 0$ or $a = -3$ have cheaper specialised formulas, so `pdbl_form` selects the one matching the curve. We use formulas from hyperelliptic database [1].


| port | direction | width |
|------|-----------|-------|
| `P0` | in        | `PointJac`, three `FIELD::W` coordinates |
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

### a = 0

`pdbl_a0` is `dbl-2009-l`. The $a$ term vanishes, so the formula has no constant multiplication. Used by curves such as BN254, BLS12-377, BLS12-381 and Secp256k1.

### a = -3

`pdbl_a3` is `dbl-2001-b`. The $a$ term is folded into a difference of squares, $3(X - Z^2)(X + Z^2)$, so again no constant multiplication is needed. Used by the NIST curves such as P-256.

### Any a

`pdbl_avar` is `dbl-2007-bl`, which works for any $a$ at the cost of one constant multiplication by $a$, built from a `l1_mod_cmul`. Used by curves such as MNT4753, where $a = 2$.

## Dependencies

- `l0_int_add` with parameters `bitwidth = FIELD::W` and `FIELD::W + 1` — through `l1_mod_add` and `l1_mod_sub`
- `l0_int_sub` with parameters `bitwidth = FIELD::W` and `FIELD::W + 1` — through `l1_mod_add` and `l1_mod_sub`
- `l0_int_mul` with parameters `bitwidth = FIELD::W` — through `l1_mod_mul` and `l1_mod_cmul`
- `l0_int_cmul` with parameters `bitwidth = FIELD::W` — through `l1_mod_mul` and `l1_mod_cmul`
- `l1_mod_add` with parameters `field` — the sums
- `l1_mod_sub` with parameters `field` — the differences
- `l1_mod_mul` with parameters `field`, `mred` — every product
- `l1_mod_cmul` with parameters `field`, `mred`, `cmul_const = a` — the product by $a$ with `pdbl_avar`

## Test Sample Generation Strategy

Every sample is a point that lies on the curve, so the kernel is only ever tested on valid group elements. The reference library generates each point by drawing a random $x$ in $\mathbb{F}_q$ and solving the curve equation for $y$, so the sample is a random point on the curve, not a random pair of field elements. Points whose double is the point at infinity are skipped, since the kernel does not represent it.

The golden output is the affine double, which the reference library computes with the group law. The testbench converts the point from affine to Jacobian coordinates and the result back, and for Montgomery designs converts each coordinate into and out of the Montgomery domain.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l2_point_dbl_sw -s sweeps/l2_point_dbl_sw.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l2_point_dbl_sw -s sweeps/l2_point_dbl_sw.yaml --only syn
```

## Authors

Gaurav Kuwar

## References

[1] Daniel J. Bernstein and Tanja Lange. Explicit-Formulas Database. https://www.hyperelliptic.org/EFD
