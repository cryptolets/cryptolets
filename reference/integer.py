"Reference implementation of integer operations"

def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def sq(a):
    return a * a

def cmul(x, const, x_w, const_w, output_type):
    "x * const, keeping the part the output type reads"
    product = x * const
    if output_type == "cmul_output_lo":
        return product & ((1 << const_w) - 1)   # the low const_w bits
    if output_type == "cmul_output_hi":
        return product >> x_w                    # everything above the input width
    return product

# TODO: Double check
def mul_par(a, b, bitwidth, skip_upper):
    """
    One schoolbook split with a partial product dropped.

    Only the half that keeps its carries is correct, which is the half a
    Barrett reduction reads. skip_upper 0 keeps the low product, 1 the high.
    """
    low = bitwidth // 2
    a0, a1 = a & ((1 << low) - 1), a >> low
    b0, b1 = b & ((1 << low) - 1), b >> low

    z0 = a0 * b0 if skip_upper == 0 else 0
    z3 = a1 * b1 if skip_upper == 1 else 0
    return z0 + ((a0 * b1) << low) + ((a1 * b0) << low) + (z3 << (2 * low))