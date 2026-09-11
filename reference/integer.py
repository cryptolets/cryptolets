"Reference implementation of integer operations"

def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b, bitwidth, output_type="mul_output_full"):
    "a * b, keeping the part the output type reads"
    product = a * b
    if output_type == "mul_output_lo":
        return product & ((1 << bitwidth) - 1)   # the low bitwidth bits
    if output_type == "mul_output_hi":
        return product >> bitwidth               # everything above the input width
    return product

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
