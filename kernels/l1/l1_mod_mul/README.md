# `l1_mod_mul` - Modular Multiplication

## Description
Multiplication in the prime field $\mathbb{F}_q$, $z = x \cdot y \bmod q$, where $0 \le x, y < q$, $0 \le z < q$ and $q$ is the prime modulus. The kernel computes the $2W$-bit product $t = x \cdot y$ with a `l0_int_mul`, then reduces it modulo $q$. A direct reduction needs a division, so this kernel supports two standard reduction algorithms that replace it with multiplications by a precomputed reduction constant, `rc`, which can either be $q'$ or $\mu$. `q_type` and `rc_type` select whether $q$ and `rc` are ports or constants baked into the hardware. A fixed constant is multiplied with a `l0_int_cmul`, a variable one with a `l0_int_mul`.

| port | direction | width |
|------|-----------|-------|
| `x`  | in        | `FIELD::W` |
| `y`  | in        | `FIELD::W` |
| `q`  | in        | `FIELD::W`, only with `var_q` |
| `rc` | in        | `FIELD::W` |
| `z`  | out       | `FIELD::W` |

Sweep design parameters:

- `bitwidth` — the width of the field elements; a named `field` sets it
- `field` — the prime field: a curve's base field, for example `bn254_base`, its scalar field, `bn254_scalar`, or `arb_field` for a random prime of the bitwidth
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

### Montgomery Reduction

Montgomery reduction keeps field elements scaled by a power of two, so the reduction divides by that power of two, a shift, instead of by $q$. The drawback is that operands must be converted into and out of this scaled domain, the Montgomery domain. The conversion is only needed once, at the start and at the end: any sequence of modular operations can run entirely in the domain, since the outputs of one are valid inputs of the next.

With `mred_mont` the scale is $R = 2^W$, so a field element $x$ is represented as $\tilde{x} = xR \bmod q$. The product of two such elements, $t = \tilde{x}\tilde{y}$, carries a factor $R^2$, and the reduction divides one $R$ out:

$$m = (t \bmod R) \cdot q' \bmod R, \quad u = (t + mq) / R$$

where $q' = -q^{-1} \bmod R$ is the reduction constant, $W$ bits wide. Adding $mq$ clears the low $W$ bits of $t$, so the division by $R$ is exact and is just a shift. $u < 2q$, so one conditional subtraction of $q$ gives $\tilde{z} = \tilde{x}\tilde{y}R^{-1} \bmod q$, the product in the Montgomery domain. The kernel does not convert; the caller supplies operands in the domain and receives the result in it.

### Barrett Reduction

Barrett reduction estimates the quotient of $t$ by $q$ with a precomputed approximation of $1/q$, then corrects the small error with conditional subtractions. It works on plain operands, so no domain conversion is needed.

With `mred_bar` the approximation is $\mu = \lfloor 2^{2W} / q \rfloor$, the reduction constant. The quotient estimate and the remainder are

$$m = \lfloor t \mu / 2^{2W} \rfloor, \quad z = t - mq$$

$m$ underestimates the true quotient by a small amount, so $t - mq$ is a few multiples of $q$ at most, and a few conditional subtractions of $q$ finish the reduction. Only the high bits of $t \mu$ are needed for $m$, so the multiplier computes a partial product rather than the full one.

### Fixed and variable constants

$q$ and `rc` ($q'$ or $\mu$) can each be fixed or variable. A fixed constant is baked into the hardware, which makes the design smaller and faster, but since the constant is hardwired the design works for one field only. A variable constant is an input port, so the same design works for any field of the bitwidth.

## Dependencies

- `l0_int_mul` with parameters `bitwidth = FIELD::W` — the product $x \cdot y$, and the products by $q$ and `rc` when variable
- `l0_int_cmul` with parameters `bitwidth = FIELD::W` — the products by $q$ and by $q'$ or $\mu$ with `fixed_q` or `fixed_rc`

## Test Sample Generation Strategy

The samples are the edge cases (`0`, `q - 1` and the midpoint, in every pairing) plus random operand pairs. The random pairs are spread across every bitwidth up to `bitwidth`, so small values are covered as well as full-width ones. Every operand is kept below the prime modulus `q`, so the samples are cryptographically sound. The golden output is $x \cdot y \bmod q$ on plain operands, which is computed in the reference library. For Montgomery designs the testbench converts the operands into and out of the Montgomery domain.

## HLS RTL Generation and Simulation

Verifies the C++, generates the RTL with HLS, then verifies the RTL with the same testbench.

```
python -m tessera run l1_mod_mul -s sweeps/l1_mod_mul.yaml --to rtl
```

## Running Logic Synthesis

Synthesizes the generated RTL to a gate netlist and reports its area, delay and power estimate.

```
python -m tessera run l1_mod_mul -s sweeps/l1_mod_mul.yaml --only syn
```

## Authors

Gaurav Kuwar, Jianqiao Mo
