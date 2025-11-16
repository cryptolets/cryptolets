from BitVector import BitVector

BITWIDTH = 256  # 2 limbs of 8 bits
WBW = 8  # b
LIMBS = BITWIDTH // WBW  # k

def bv(val, bits):
    return BitVector(intVal=val, size=bits)

def mul_f(x, y, bits):
    # Fixed-width multiplication, result is 2*bits
    prod = (x.intValue() * y.intValue()) & ((1 << (2*bits)) - 1)
    return bv(prod, 2*bits)

def mul_f_gen(a, b, bitwidth_a, bitwidth_b):
    # Fixed-width multiplication, result is bitwidth_a + bitwidth_b bits
    prod = (a.intValue() * b.intValue()) & ((1 << (bitwidth_a + bitwidth_b)) - 1)
    return bv(prod, bitwidth_a + bitwidth_b)

def mask_bv(val, bits):
    return bv(val.intValue() & ((1 << bits) - 1), bits)

def modmul_barrett_core(x, y, m, mu):
    # All inputs are BitVector
    t = mul_f(x, y, BITWIDTH)  # t = 2 x BITWIDTH
    mu = bv(mu.intValue(), 2*LIMBS*WBW)  # mu = 2*k*bw

    # 1. q1 = floor(x / b^{k-1})
    x_full = bv(t.intValue(), 2*LIMBS*WBW)
    q1 = bv(x_full.intValue() >> (WBW * (LIMBS - 1)), LIMBS*WBW+1)

    # 1. q2 = q1 * mu
    q2 = mul_f_gen(q1, mu, q1.size, mu.size)  # q1.size=LIMBS*WBW+1, mu.size=2*LIMBS*WBW
    q2_full = q2

    # 1. q3 = floor(q2 / b^{k+1})
    q3 = bv(q2_full.intValue() >> (WBW * (LIMBS + 1)), LIMBS*WBW+1)

    # 2. r1 = x mod b^{k+1}
    r1 = mask_bv(x_full, (LIMBS + 1) * WBW)

    # 2. r2 = (q3 * m) mod b^{k+1}
    m_full = m
    q3m = mul_f_gen(q3, m_full, q3.size, m_full.size)
    r2 = mask_bv(q3m, (LIMBS + 1) * WBW)

    # 2. r = r1 - r2
    r = r1.intValue() - r2.intValue()

    # 3. If r < 0 then r = r + b^{k+1}
    if r < 0:
        r += 1 << ((LIMBS + 1) * WBW)

    # 4. While r >= m_full.intValue() do: r = r - m_full
    while r >= m_full.intValue():
        r -= m_full.intValue()

    # 5. Return r as wide_t (BITWIDTH bits)
    return bv(r, BITWIDTH)

def main():
    m = bv(251, BITWIDTH)
    mu_val = (1 << (2 * BITWIDTH)) // m.intValue()
    mu = bv(mu_val, 2*BITWIDTH)

    x = bv(200, BITWIDTH)
    y = bv(150, BITWIDTH)

    result = modmul_barrett_core(x, y, m, mu)
    print(f"modmul_barrett_core({x.intValue()}, {y.intValue()}, {m.intValue()}, {mu.intValue()}) = {result.intValue()}")

    expected = (x.intValue() * y.intValue()) % m.intValue()
    print(f"Expected: {expected}")

    # Additional test: x = m-1, y = m-1
    x2 = bv(m.intValue() - 1, BITWIDTH)
    y2 = bv(m.intValue() - 1, BITWIDTH)
    result2 = modmul_barrett_core(x2, y2, m, mu)
    print(f"modmul_barrett_core({x2.intValue()}, {y2.intValue()}, {m.intValue()}, {mu.intValue()}) = {result2.intValue()}")
    expected2 = (x2.intValue() * y2.intValue()) % m.intValue()
    print(f"Expected: {expected2}")

    # Test with x=0, y=0, custom modulus and mu
    m3_val = 94638212182620952513693670343372186519186500347741441943556257891053441384207
    mu3_val = 141674357753820316679329870488098374742204720258753741045413765197694209102774
    m3 = bv(m3_val, BITWIDTH)
    mu3 = bv(mu3_val, 2*BITWIDTH)
    x3 = bv(0, BITWIDTH)
    y3 = bv(0, BITWIDTH)
    result3 = modmul_barrett_core(x3, y3, m3, mu3)
    print(f"modmul_barrett_core({x3.intValue()}, {y3.intValue()}, {m3.intValue()}, {mu3.intValue()}) = {result3.intValue()}")
    expected3 = (x3.intValue() * y3.intValue()) % m3.intValue()
    print(f"Expected: {expected3}")

if __name__ == "__main__":
    main()