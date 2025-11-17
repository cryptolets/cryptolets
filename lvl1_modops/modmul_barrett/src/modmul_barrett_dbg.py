from BitVector import BitVector
import math

BITWIDTH = 256  # 2 limbs of 8 bits
WBW = 8  # b
B_EXP = int(math.log2(WBW))
LIMBS = math.ceil(BITWIDTH / B_EXP)  # k

def bv(val, bits):
    # Store negative values in two's complement representation
    val = val % (1 << bits)
    return BitVector(intVal=val, size=bits)

def mul_f(x, y, bits):
    # Fixed-width multiplication, result is 2*bits
    prod = (x.intValue() * y.intValue()) & ((1 << (2*bits)) - 1)
    return bv(prod, 2*bits)

# def mul_f_gen(a, b, bitwidth_a, bitwidth_b):
#     # Fixed-width multiplication, result is bitwidth_a + bitwidth_b bits
#     prod = (a.intValue() * b.intValue()) & ((1 << (bitwidth_a + bitwidth_b)) - 1)
#     return bv(prod, bitwidth_a + bitwidth_b)

def mul_f_gen(a, b, bitwidth_a, bitwidth_b):
    # Emulate multi-precision multiplication using only WBW-bit multiplications
    # a, b: BitVector
    # bitwidth_a, bitwidth_b: total bitwidths of a and b
    # Returns BitVector of bitwidth_a + bitwidth_b

    num_limbs_a = (bitwidth_a + WBW - 1) // WBW
    num_limbs_b = (bitwidth_b + WBW - 1) // WBW
    result_bits = bitwidth_a + bitwidth_b
    result = 0

    # Extract limbs
    a_val = a.intValue()
    b_val = b.intValue()
    a_limbs = [(a_val >> (i * WBW)) & ((1 << WBW) - 1) for i in range(num_limbs_a)]
    b_limbs = [(b_val >> (i * WBW)) & ((1 << WBW) - 1) for i in range(num_limbs_b)]

    # Schoolbook multiplication
    partials = [0] * (num_limbs_a + num_limbs_b)
    for i in range(num_limbs_a):
        carry = 0
        for j in range(num_limbs_b):
            idx = i + j
            prod = (a_limbs[i] * b_limbs[j]) + partials[idx] + carry
            partials[idx] = prod & ((1 << WBW) - 1)
            carry = prod >> WBW
        partials[i + num_limbs_b] = carry

    # Combine limbs into result
    for i in range(len(partials)):
        result |= (partials[i] << (i * WBW))

    # Mask to result_bits
    result &= (1 << result_bits) - 1
    return bv(result, result_bits)

def mask_bv(val, bits):
    return bv(val.intValue() & ((1 << bits) - 1), bits)

def modmul_barrett_core(x, y, m, mu, debug=False):
    # All inputs are BitVector

    t = mul_f(x, y, BITWIDTH)  # t = 2 x BITWIDTH
    mu = bv(mu.intValue(), 2 * LIMBS * B_EXP - BITWIDTH + 1)  # mu = bv(mu.intValue(), LIMBS*B_EXP+1)
    if debug:
        print(f"t = {hex(t.intValue())}")
        print(f"mu = {hex(mu.intValue())}")

    # 1. q1 = floor(x / b^{k-1})
    x_full = bv(t.intValue(), 2 * LIMBS * B_EXP)  # x_full = bv(t.intValue(), 2*BITWIDTH)  # x_full = bv(t.intValue(), 2*LIMBS*B_EXP)
    q1 = bv(x_full.intValue() >> (B_EXP * (LIMBS - 1)), (LIMBS + 1)*B_EXP)
    if debug:
        print(f"x_full = {hex(x_full.intValue())}")
        print(f"q1 = {hex(q1.intValue())}")

    # 1. q2 = q1 * mu
    q2 = mul_f_gen(q1, mu, q1.size, mu.size)  # q1.size=(LIMBS+1)*B_EXP, mu.size=LIMBS*B_EXP
    q2_full = bv(q2.intValue(), (3 * LIMBS + 1) * B_EXP - BITWIDTH + 1)  # q2_full = bv(q2.intValue(), (2 * LIMBS + 1) * B_EXP + 1)
    if debug:
        print(f"q2 = {hex(q2.intValue())}")
        print(f"q2_full = {hex(q2_full.intValue())}")

    # 1. q3 = floor(q2 / b^{k+1})
    q3 = bv(q2_full.intValue() >> (B_EXP * (LIMBS + 1)), 2*LIMBS*B_EXP-BITWIDTH+1)  # q3 = bv(q2_full.intValue() >> (B_EXP * (LIMBS + 1)), 2LIMBS*B_EXP+1)
    if debug:
        print(f"q3 = {hex(q3.intValue())}")

    # 2. r1 = x mod b^{k+1}
    r1 = mask_bv(x_full, (LIMBS + 1) * B_EXP)
    if debug:
        print(f"r1 = {hex(r1.intValue())}")

    # 2. r2 = (q3 * m) mod b^{k+1}
    q3m = mul_f_gen(q3, m, q3.size, m.size)
    r2 = mask_bv(q3m, (LIMBS + 1) * B_EXP)
    if debug:
        print(f"q3m = {hex(q3m.intValue())}")
        print(f"r2 = {hex(r2.intValue())}")

    # 2. r = r1 - r2
    r = bv(r1.intValue() - r2.intValue(), (LIMBS + 1) * B_EXP + 1)
    if debug:
        print(f"r (before correction) = {hex(r.intValue())}")
    # r = r.intValue()  # Convert back to int for subsequent arithmetic

    # 3. If r < 0 then r = r + b^{k+1}
    # Check if r is negative by inspecting the MSB
    if (r.intValue() >> (r.size - 1)) & 1:
        r = bv(r.intValue() + (1 << ((LIMBS + 1) * B_EXP)), r.size)
        if debug:
            print(f"r (after correction) = {hex(r.intValue())}")

    # 4. While r >= m_full.intValue() do: r = r - m_full
    m_full = bv(m.intValue(), (LIMBS) * B_EXP)  # m_full = bv(m.intValue(), BITWIDTH)
    if debug:
        print(f"m_full = {hex(m_full.intValue())}")
    while r.intValue() >= m_full.intValue():
        r = bv(r.intValue() - m_full.intValue(), r.size)
        if debug:
            print(f"r (in loop) = {hex(r.intValue())}")

    if debug:
        print(f"r (final) = {hex(r.intValue())}")
    # 5. Return r as wide_t (BITWIDTH bits)
    return bv(r.intValue(), BITWIDTH)

def main():
    if WBW & (WBW - 1) != 0 or WBW == 0:
        raise ValueError(f"WBW must be a power of 2, but got {WBW}")
    if BITWIDTH & (BITWIDTH - 1) != 0 or BITWIDTH == 0:
        raise ValueError(f"BITWIDTH must be a power of 2, but got {BITWIDTH}")

    dbg = False
    
    m = bv(94638212182620952513693670343372186519186500347741441943556257891053441384207, BITWIDTH)
    mu_val = (WBW ** (2 * LIMBS)) // m.intValue()
    mu = bv(mu_val, 2 * LIMBS * B_EXP - BITWIDTH + 1)  # mu = bv(mu_val, BITWIDTH + 1)

    x = bv(200, BITWIDTH)
    y = bv(150, BITWIDTH)

    result = modmul_barrett_core(x, y, m, mu, dbg)
    print(f"modmul_barrett_core({x.intValue()}, {y.intValue()}, {m.intValue()}, {mu.intValue()}) = {result.intValue()}")

    expected = (x.intValue() * y.intValue()) % m.intValue()
    print(f"Expected: {expected}")
    print("Fail" if result.intValue() != expected else "Pass")

    # Additional test: x = m-1, y = m-1
    x2 = bv(m.intValue() - 1, BITWIDTH)
    y2 = bv(m.intValue() - 1, BITWIDTH)
    result2 = modmul_barrett_core(x2, y2, m, mu, dbg)
    print(f"modmul_barrett_core({x2.intValue()}, {y2.intValue()}, {m.intValue()}, {mu.intValue()}) = {result2.intValue()}")
    expected2 = (x2.intValue() * y2.intValue()) % m.intValue()
    print(f"Expected: {expected2}")
    print("Fail" if result2.intValue() != expected2 else "Pass")

    dbg = True

    m3_val = 94638212182620952513693670343372186519186500347741441943556257891053441384207
    mu3_val = WBW ** (2 * LIMBS) // m3_val
    m3 = bv(m3_val, BITWIDTH)
    mu3 = bv(mu3_val, 2 * LIMBS * B_EXP - BITWIDTH + 1)  # mu3 = bv(mu3_val, 2*BITWIDTH)
    x3 = bv(10576938527347621454938657332657860667041742158949561047950663058429844127864, BITWIDTH)
    y3 = bv(10576938527347621454938657332657860667041742158949561047950663058429844127864, BITWIDTH)
    result3 = modmul_barrett_core(x3, y3, m3, mu3, dbg)
    print(f"modmul_barrett_core({x3.intValue()}, {y3.intValue()}, {m3.intValue()}, {mu3.intValue()}) = {result3.intValue()}")
    expected3 = (x3.intValue() * y3.intValue()) % m3.intValue()
    print(f"Expected: {expected3}")
    print("Fail" if result3.intValue() != expected3 else "Pass")

    # Additional sample with x and y = 21153877054695242909877314665315721334083484317899122095901326116859688255728
    x4 = bv(21153877054695242909877314665315721334083484317899122095901326116859688255728, BITWIDTH)
    y4 = bv(21153877054695242909877314665315721334083484317899122095901326116859688255728, BITWIDTH)
    result4 = modmul_barrett_core(x4, y4, m3, mu3, dbg)
    print(f"modmul_barrett_core({x4.intValue()}, {y4.intValue()}, {m3.intValue()}, {mu3.intValue()}) = {result4.intValue()}")
    expected4 = (x4.intValue() * y4.intValue()) % m3.intValue()
    print(f"Expected: {expected4}")
    print("Fail" if result4.intValue() != expected4 else "Pass")

if __name__ == "__main__":
    main()