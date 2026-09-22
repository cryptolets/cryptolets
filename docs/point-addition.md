# Point Addition

[Back to the README](../README.md)

Cryptolets expresses a point-addition (PADD) formula as a C++ sequence of modular operations. Adding a curve supported by an existing formula is a configuration change; adding a coordinate system requires a corresponding formula and point representation.

This guide scaffolds the step-by-step tutorial. The complete worked example for a new formula remains to be added; the code excerpt below illustrates the existing implementation pattern.

## Existing Implementations

| Kernel | Reference |
|---|---|
| `point_add` | [Short Weierstrass addition in Jacobian coordinates](../lvl2/point_add/src/point_add.cpp) |
| `point_double` | [Short Weierstrass doubling](../lvl2/point_double/src/point_double.cpp) |
| `point_add_te` | [Twisted Edwards addition in extended coordinates](../lvl2/point_add_te/src/point_add_te.cpp) |
| `point_add_cyclonemsm` | [CycloneMSM-style point addition](../lvl2/point_add_cyclonemsm/src/point_add_cyclonemsm.cpp) |

Shared Python references are in [padd_sw_models.py](../lvl2/common/padd_sw_models.py) and [padd_te_models.py](../lvl2/common/padd_te_models.py). Each kernel has its own sample generator and C++ testbench.

## Adding a Curve

1. Add an entry to [field_const.json](../field_const.json), following a curve of the same form. Supply `form`, `a`, `q`, and integer `bitwidth`, plus the formula's coefficients (`b` for Weierstrass, or `d` and `k` where used for Twisted Edwards). Field values are hexadecimal strings.
2. Select the entry's name in the sweep's `CURVE_TYPE`. The framework derives the width and its supported assumption about `a` from this entry.
3. Check that the chosen kernel supports the curve form and coefficient assumptions. Field-only entries with `form: N/A` are not point-addition curves.
4. Check multiplier-width maps and fixed/variable parameter settings in the sweep. The sweep filters can remove named-curve configurations that are equivalent to generic variable-parameter designs.
5. Preview the generated configurations, then validate the curve with the kernel's sample generator and testbench on the configured tool machine.

## Adding a PADD Formula or Coordinate System

### 1. Choose the formula and reference kernel

Record the formula source, curve assumptions, coordinate definitions, and supported inputs. Start from the closest existing kernel. Keep a distinct kernel name when the implementation needs to be compared independently.

### 2. Define the point representation

Reuse an existing point type from [primitives.h](../utils/include/primitives.h) when its meaning matches the formula. Otherwise define a type in the new kernel's header, with a field for each coordinate. Specify how coordinates map to an affine point and how the identity is represented.

### 3. Express the formula using modular operations

Use the [ModOps backend](../lvl1_modops/include/modops.h) to access modular addition, subtraction, multiplication, squaring, and doubling. The existing kernels separate the formula from the wrapper that supplies the modulus, reduction constants, and curve parameters.

For example, the Weierstrass implementation computes these intermediate values:

```cpp
wide_t Z1Z1 = be.modsq(P0.Z);
wide_t Z2Z2 = be.modsq(P1.Z);
wide_t U1 = be.modmul(P0.X, Z2Z2);
wide_t U2 = be.modmul(P1.X, Z1Z1);
```

Continue this pattern for the new formula's operation sequence and output coordinates. Keep operands and constants in the domain expected by the selected backend: Montgomery arithmetic uses Montgomery-encoded field values.

**Worked-example TODO:** choose a new formula and provide its complete point type, C++ implementation, wrapper, and matching file changes. This excerpt is not a complete new PADD implementation.

### 4. Adapt the reference and test data

Add a software reference, generate valid input points in the new coordinates, and update the testbench's CSV fields and output checks. Compare mathematical points after coordinate conversion where coordinate tuples are not unique. Include the identity, doubling, and inverse-point inputs when the formula promises to support them; document any exclusions.

### 5. Register and evaluate the new kernel

Follow [Extending the Framework](extending.md#catapult-integration) for Tcl setup, configuration, naming, and registration. The existing PADD Tcl script has kernel-specific dependencies and directives, so a new kernel may require more than adding a registry entry.

Start with C++ verification, then RTL verification and a small sweep. Use the root README's [analysis instructions](../README.md#analyze-results) to compare area and latency with the reference implementation.
