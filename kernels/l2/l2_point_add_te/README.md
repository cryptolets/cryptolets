# `l2_point_add_te` - Point Addition (Twisted Edwards)

## Description
Addition of two points on an elliptic curve. This kernel targets the Twisted Edwards form, $ax^2 + y^2 = 1 + dx^2y^2$. The points are in extended projective coordinates $(X, Y, Z, T)$, which represent the affine point $(X/Z, Y/Z)$ with $T = XY/Z$, and avoid the field inversion that affine addition needs. Twisted Edwards addition formulas are unified: the same formula adds two distinct points and doubles a point, so unlike Short Weierstrass no separate doubling path is needed. `padd_te_form` selects one of two formulas from the Explicit-Formulas Database [1].

| port | direction | width |
|------|-----------|-------|
| `P0` | in        | `PointExtProj`, four `FIELD::W` coordinates |
| `P1` | in        | `PointExtProj`, four `FIELD::W` coordinates |
| `q`  | in        | `FIELD::W`, only with `var_q` |
| `rc` | in        | `FIELD::W` |
| `R`  | out       | `PointExtProj`, four `FIELD::W` coordinates |

Sweep design parameters:

- `bitwidth` — the width of the field elements; the `field` sets it
- `field` — the curve's base field, for example `ed25519_base`
- `padd_te_form` — the addition formula: `padd_te_add` or `padd_te_cyclone`
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

### General addition

`padd_te_add` is `add-2008-hwcd`, a unified addition formula that works for any $a$ and $d$. It multiplies by both curve coefficients, $a$ and $d$.

### CycloneMSM addition

`padd_te_cyclone` is the formula used by CycloneMSM [2], `add-2008-hwcd-3`, a unified addition formula that requires $a = -1$. The coefficient $a$ then disappears, and the single remaining constant is $k = 2d$, so the formula has one constant multiplication instead of two and fewer operations overall. Curves such as Ed25519 are defined with $a = -1$ for this reason.

## Dependencies

- `l0_int_add` with parameters `bitwidth = FIELD::W` and `FIELD::W + 1` — through `l1_mod_add` and `l1_mod_sub`
- `l0_int_sub` with parameters `bitwidth = FIELD::W` and `FIELD::W + 1` — through `l1_mod_add` and `l1_mod_sub`
- `l0_int_mul` with parameters `bitwidth = FIELD::W` — through `l1_mod_mul` and `l1_mod_cmul`
- `l0_int_cmul` with parameters `bitwidth = FIELD::W` — through `l1_mod_mul` and `l1_mod_cmul`
- `l1_mod_add` with parameters `field` — the sums
- `l1_mod_sub` with parameters `field` — the differences
- `l1_mod_mul` with parameters `field`, `mred` — every product of two variables
- `l1_mod_cmul` with parameters `field`, `mred`, `cmul_const = a` and `d`, or `k` — the products by the curve coefficients

## Test Sample Generation Strategy

Every sample is a pair of points that lie on the curve, so the kernel is only ever tested on valid group elements. The reference library generates each point by drawing a random $x$ in $\mathbb{F}_q$ and solving the curve equation for $y$, so the pair is a random point on the curve, not a random pair of field elements. Since the formula is unified, no equal-point samples are needed. Pairs whose sum is the point at infinity are skipped, since the kernel does not represent it.

The golden output is the affine sum, which the reference library computes with the group law. The testbench converts the points from affine to extended projective coordinates and the result back, and for Montgomery designs converts each coordinate into and out of the Montgomery domain.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l2_point_add_te -s sweeps/l2_point_add_te.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l2_point_add_te -s sweeps/l2_point_add_te.yaml --only syn
```

## Authors

Gaurav Kuwar

## References

[1] Daniel J. Bernstein and Tanja Lange. Explicit-Formulas Database. https://www.hyperelliptic.org/EFD

[2] Kaveh Aasaraai, Don Beaver, Emanuele Cesena, Rahul Maganti, Nicolas Stalder, and Javier Varela. 2022. FPGA Acceleration of Multi-Scalar Multiplication: CycloneMSM. Cryptology ePrint Archive, Paper 2022/1396. https://eprint.iacr.org/2022/1396
