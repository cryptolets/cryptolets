# Point Addition

[Back to the README](../README.md)

Locus writes each point-addition (PADD) formula as a C++ sequence of modular operations. To add a curve for an existing formula, you change only the configuration. To add a formula or coordinate system, you add a new kernel.

This tutorial is a case study with the Pasta curves (Pallas and Vesta) as the example. The case study adds the two curves, then adds a new formula for them: complete addition from Algorithm 8 of [Renes, Costello, and Batina](https://eprint.iacr.org/2015/1060.pdf) (RCB). This formula adds a projective point and an affine point on a short Weierstrass curve with `a = 0`.

## Existing Implementations

| Kernel | Reference |
|---|---|
| `point_add` | [Short Weierstrass addition in Jacobian coordinates](../lvl2/point_add/src/point_add.cpp) |
| `point_double` | [Short Weierstrass doubling](../lvl2/point_double/src/point_double.cpp) |
| `point_add_te` | [Twisted Edwards addition in extended coordinates](../lvl2/point_add_te/src/point_add_te.cpp) |
| `point_add_cyclonemsm` | [CycloneMSM-style point addition](../lvl2/point_add_cyclonemsm/src/point_add_cyclonemsm.cpp) |
| `point_add_rcb` | [RCB complete addition, projective + affine, `a = 0`](../lvl2/point_add_rcb/src/point_add_rcb.cpp) (the case study in this guide) |

The Python reference models are in [padd_sw_models.py](../lvl2/common/padd_sw_models.py) and [padd_te_models.py](../lvl2/common/padd_te_models.py). Each kernel has its own sample generator and C++ testbench.

## Adding a Curve

1. Add an entry to [field_const.json](../field_const.json). Use hexadecimal strings for field values. For Pallas:

   ```json
   "PALLAS": {
     "form": "Weierstrass",
     "desc": "https://github.com/zcash/pasta_curves/blob/main/README.md",
     "a": "0",
     "b": "5",
     "q": "0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001",
     "bitwidth": 255
   }
   ```

   Vesta is the same, with `q = 0x40000000000000000000000000000000224698fc0994a8dd8c46eb2100000001`.

2. Set `CURVE_TYPE: [PALLAS, VESTA]` in the sweep. The framework reads the bitwidth and `a` from the entry.
3. Make sure that the kernel supports the curve form and value of `a`. The existing `point_add` supports Pallas and Vesta because `a = 0`.
4. Make sure that the `BASE_MUL_WIDTH` and `KAR_BASE_MUL_WIDTH` maps have an entry for the curve bitwidth (255).

The steps that follow add the RCB formula as a new kernel, `point_add_rcb`.

## Adding a PADD Formula or Coordinate System

### 1. Add the point type

RCB uses projective coordinates, where the affine point is `(X/Z, Y/Z)`. Add this type to [primitives.h](../utils/include/primitives.h) next to `EC_point_J`:

```cpp
// Projective coordinates
typedef struct {
    wide_t X;
    wide_t Y;
    wide_t Z;
} EC_point_P;
```

The second input uses the existing affine type, `EC_point_A`.

### 2. Add the curve constant

The formula multiplies by `b3 = 3b`. Every curve constant goes through the same chain of files, so add `b3` to each:

1. [common.py](../utils/common.py): add `"b3"` to `FIELD_CONTS`. The params.h generator then writes `FIELD_B3_HEX`, `FIELD_B3_MONT_HEX`, and their NAF arrays for every curve. The value is 0 when the curve has no `b`.
2. [gen_params_h.py](../utils/gen_params_h.py): if a curve entry has `b` but no `b3`, calculate `b3 = 3b mod q`. Named curves then do not need a `b3` field.
3. [gen_field_const.py](../utils/gen_field_const.py): add `b3` to the random-curve constants.
4. [primitives.h](../utils/include/primitives.h): declare `FIELD_B3_MONT`, `FIELD_B3_INT`, and their NAF arrays, as for `FIELD_K`.
5. [cmul_f](../lvl0_primitives/cmul_f/): add `cmul_field_b3_mont()` and `cmul_field_b3()`.
6. [modmul_mont](../lvl1_modops/modmul_mont/) and [modmul_barrett](../lvl1_modops/modmul_barrett/): add `cmodmul_b3_mont_core()` and `cmodmul_b3_barrett_core()`. Each one calls the constant multiplier, then reduces.
7. [modops.h](../lvl1_modops/include/modops.h): add `cmodmul_b3()` to `ModOps` for both backends.

For example, the Montgomery version in `modmul_mont.cpp` is:

```cpp
#ifdef FIELD_B3_MONT_HEX
    wide_t cmodmul_b3_mont_core(const wide_t x, const wide_t q, const wide_t q_prime) {
        wide_2x_t t = cmul_field_b3_mont(x); // compile to constant multiplier
        return mont_reduction(t, q, q_prime);
    }
#endif
```

### 3. Write the formula

Create `lvl2/point_add_rcb/` with `include/point_add_rcb.h` and `src/point_add_rcb.cpp`. Write each line of the algorithm as one `ModOps` call:

```cpp
EC_point_P point_add_rcb_core(
    EC_point_P P0, EC_point_A P1, const ModOps& be, const wide_t field_b3
) {
    EC_point_P result;

    wide_t t0 = be.modmul(P0.X, P1.x);      //  1. t0 = X1*x2
    wide_t t1 = be.modmul(P0.Y, P1.y);      //  2. t1 = Y1*y2
    wide_t t3 = be.modadd(P1.x, P1.y);      //  3. t3 = x2+y2
    wide_t t4 = be.modadd(P0.X, P0.Y);      //  4. t4 = X1+Y1
    t3        = be.modmul(t3, t4);          //  5. t3 = t3*t4
    t4        = be.modadd(t0, t1);          //  6. t4 = t0+t1
    t3        = be.modsub(t3, t4);          //  7. t3 = t3-t4
    t4        = be.modmul(P1.y, P0.Z);      //  8. t4 = y2*Z1
    t4        = be.modadd(t4, P0.Y);        //  9. t4 = t4+Y1
    result.Y  = be.modmul(P1.x, P0.Z);      // 10. Y3 = x2*Z1
    result.Y  = be.modadd(result.Y, P0.X);  // 11. Y3 = Y3+X1
    result.X  = be.moddouble(t0);           // 12. X3 = t0+t0
    t0        = be.modadd(result.X, t0);    // 13. t0 = X3+t0

    #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
        wide_t t2 = be.cmodmul_b3(P0.Z);        // 14. t2 = b3*Z1 (constant)
    #else
        wide_t t2 = be.modmul(field_b3, P0.Z);  // 14. t2 = b3*Z1
    #endif

    result.Z  = be.modadd(t1, t2);          // 15. Z3 = t1+t2
    t1        = be.modsub(t1, t2);          // 16. t1 = t1-t2

    #if CURVE_PARAMS_TYPE == FIXED_CURVE_PARAMS
        result.Y = be.cmodmul_b3(result.Y);        // 17. Y3 = b3*Y3 (constant)
    #else
        result.Y = be.modmul(field_b3, result.Y);  // 17. Y3 = b3*Y3
    #endif

    result.X  = be.modmul(t4, result.Y);    // 18. X3 = t4*Y3
    t2        = be.modmul(t3, t1);          // 19. t2 = t3*t1
    result.X  = be.modsub(t2, result.X);    // 20. X3 = t2-X3
    result.Y  = be.modmul(result.Y, t0);    // 21. Y3 = Y3*t0
    t1        = be.modmul(t1, result.Z);    // 22. t1 = t1*Z3
    result.Y  = be.modadd(t1, result.Y);    // 23. Y3 = t1+Y3
    t0        = be.modmul(t0, t3);          // 24. t0 = t0*t3
    result.Z  = be.modmul(result.Z, t4);    // 25. Z3 = Z3*t4
    result.Z  = be.modadd(result.Z, t0);    // 26. Z3 = Z3+t0
    return result;
}
```

With `FIXED_CURVE_PARAMS`, Catapult builds the `b3` multiplications as constant multipliers. With `VAR_CURVE_PARAMS`, `field_b3` is an input.

Then add the public function `point_add_rcb()`. Copy the wrapper from [point_add.cpp](../lvl2/point_add/src/point_add.cpp). The wrapper takes `q`, the reduction constant, and `field_b3` as inputs when they are variable, and uses the generated constants when they are fixed. It then builds the `ModOps` backend and calls `point_add_rcb_core()`. Use Montgomery-encoded values with the Montgomery backend. For example, a fixed `field_b3` is `FIELD_B3_MONT`, not `FIELD_B3_INT`.

### 4. Add the reference model and tests

1. In [padd_sw_models.py](../lvl2/common/padd_sw_models.py), add `point_add_sw_rcb_ref()`. It uses the same 26 steps as the C++ code, with Python `modmul`, `modadd`, and `modsub`.
2. In [field_helpers.py](../utils/field_helpers.py), add an `EC_point_P` class and `aff_to_proj()` and `proj_to_aff()` to `ShortWeierstrass`. `aff_to_proj()` uses a random `Z`, so the tests use different projective inputs for the same point.
3. Copy `gen_samples.py` from `point_add`. Keep its command-line arguments (`--bw`, `--n`, `--curve_type`, `--modmul-type`, and the file paths), so that the Tcl flow can call it without changes. Change it to write `X1, Y1, Z1, X2, Y2`, the reduction constants, and `field_b3`. Write `X3, Y3, Z3` as the golden output. Convert all values to the Montgomery domain when the backend is Montgomery.
4. In the generator, compare each result with affine addition (`E.add`). Also make sure that each point is on the curve. Include `P1 == P2` samples, because a complete formula must also double.
5. Copy the testbench from `point_add` and change the CSV fields and the call to `point_add_rcb()`.

### 5. Register and run

1. In [run_config.yaml](../configs/run_config.yaml), add `point_add_rcb` to `KERNELS`, to `padd_sw` in `SWEEP_GROUP_MAP`, and to `padd` in `CORE_GROUP_MAP`. The kernel then uses [catapult_padd_core.tcl](../tcl_cores/catapult_padd_core.tcl).
2. In `catapult_padd_core.tcl`, make `cmodmul_b3` a CCORE, the same as `cmodmul_k`. If you do not, Catapult puts the `b3` multiplier inline.
   1. Add a flag that is true for `point_add_rcb` with `FIXED_CURVE_PARAMS`:

      ```tcl
      set HAS_CMODMUL_B3 [expr {
          $CURVE_PARAMS_TYPE eq "FIXED_CURVE_PARAMS" &&
          $KERNEL_NAME eq "point_add_rcb"
      }]
      ```

   2. Search for `cmodmul_k` and `cmul_field_k`. At each result, add the same line or block for `b3`. There are 9 locations, which include the `global` list in `modmul_run`.
3. Create a sweep for the case study. [padd_rcb_pasta_sweep.yaml](../custom_sweeps_configs/padd_rcb_pasta_sweep.yaml) is a copy of `padd_sw_sweep.yaml` with these changes:

   ```yaml
   BITWIDTH: [255]
   CURVE_TYPE: [PALLAS, VESTA, RAND_CURVE]
   FIELD_A: [A0]  # RCB needs a = 0
   CURVE_PARAMS_TYPE: [FIXED_CURVE_PARAMS, VAR_CURVE_PARAMS]
   Q_TYPE: [FIXED_Q, VAR_Q]
   REDC_TYPE: [FIXED_RC, VAR_RC]

   BASE_MUL_WIDTH:
     255: [63]

   KAR_BASE_MUL_WIDTH:
     255: [127]
   ```

   The sweep makes 15 configurations. For each named curve, the framework removes the all-variable design because it is the same as the `RAND_CURVE` design.

4. Do a C++ test first. Set `TEST: true` and `TEST_ONLY: true` in the sweep, then run:

   ```bash
   python3 run.py point_add_rcb \
     --sweep-file custom_sweeps_configs/padd_rcb_pasta_sweep.yaml \
     --core-script tcl_cores/catapult_padd_core.tcl \
     --threads 16 --tp 1
   ```

5. Set `TEST_ONLY: false` and run the same command again. This does HLS and verifies the RTL. Then compare the results:

   ```bash
   python3 analyze.py lvl2/point_add_rcb -t
   python3 analyze.py lvl2/point_add_rcb -t --curve PALLAS
   ```

For Tcl setup, naming, and other registration details, see [Extending the Framework](extending.md#catapult-integration).
