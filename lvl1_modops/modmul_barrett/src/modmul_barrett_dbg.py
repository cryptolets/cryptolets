# Emmulation and debugging of modmul_barrett multi-precision logic
from BitVector import BitVector
import math

BITWIDTH = 256
WBW = 4
B_REAL = 2 ** WBW  # b
LIMBGROUPS = int((BITWIDTH + WBW - 1) / WBW)  # math.ceil(BITWIDTH / WBW)  # k

def bv(val, bits):
    # Store negative values in two's complement representation
    val = val % (1 << bits)
    return BitVector(intVal=val, size=bits)

def mul_f(x, y, bits):
    # Fixed-width multiplication, result is 2*bits
    prod = (x.intValue() * y.intValue()) & ((1 << (2*bits)) - 1)
    return bv(prod, 2*bits)

def mul_f_gen(a, b, bitwidth_a, bitwidth_b):
    # Fixed-width multiplication, result is bitwidth_a + bitwidth_b bits
    prod = (a.intValue() * b.intValue()) & ((1 << (bitwidth_a + bitwidth_b)) - 1)
    return bv(prod, bitwidth_a + bitwidth_b)

def mul_f_WBW(a, b):
    # Fixed-width multiplication, result is 2*WBW bits
    assert a.size == WBW, f"Expected a.size == {WBW}, got {a.size}"
    assert b.size == WBW, f"Expected b.size == {WBW}, got {b.size}"
    prod = (a.intValue() * b.intValue()) & ((1 << (2*WBW)) - 1)
    return bv(prod, 2*WBW)

def mask_bv(val, bits):
    return bv(val.intValue() & ((1 << bits) - 1), bits)

def modmul_barrett_core(x, y, m, mu, debug=False):
    # All inputs are BitVector

    t = mul_f(x, y, BITWIDTH)  # t = 2 x BITWIDTH
    mu = bv(mu.intValue(), 2 * LIMBGROUPS * WBW - BITWIDTH + 1)  # mu = bv(mu.intValue(), LIMBGROUPS*WBW+1)
    if debug:
        print(f"t = {hex(t.intValue())}")
        print(f"mu = {hex(mu.intValue())}")
    m = bv(m.intValue(), LIMBGROUPS * WBW)

    # 1. q1 = floor(x / b^{k-1})
    x_full = bv(t.intValue(), 2 * LIMBGROUPS * WBW)  # x_full = bv(t.intValue(), 2*BITWIDTH)  # x_full = bv(t.intValue(), 2*LIMBGROUPS*WBW)
    q1 = bv(x_full.intValue() >> (WBW * (LIMBGROUPS - 1)), (LIMBGROUPS + 1)*WBW)
    if debug:
        print(f"x_full = {hex(x_full.intValue())}")
        print(f"q1 = {hex(q1.intValue())}")

    # 1. q2 = q1 * mu
    # q2_expect = mul_f_gen(q1, mu, q1.size, mu.size)  # q1.size=(LIMBGROUPS+1)*WBW, mu.size=LIMBGROUPS*WBW
    # if debug:
    #     print(f"Expected q2 = {hex(q2_expect.intValue())}")
    # 1. q2 = q1 * mu (schoolbook, WBW-bit multiplier only)
    q2_bits = (3 * LIMBGROUPS + 1) * WBW - BITWIDTH + 1
    q2 = bv(0, q2_bits)
    for i in range((BITWIDTH + WBW - 1) // WBW + 1):
        c = bv(0, WBW)  # carry
        for j in range((BITWIDTH + WBW - 1) // WBW + 1):
            q1_limb = bv((q1.intValue() >> (i * WBW)) & ((1 << WBW) - 1), WBW)
            mu_limb = bv((mu.intValue() >> (j * WBW)) & ((1 << WBW) - 1), WBW)
            prod_bv = mul_f_WBW(q1_limb, mu_limb)

            q2_ij = bv((q2.intValue() >> ((i + j) * WBW)) & ((1 << WBW) - 1), WBW)
            uv = bv(q2_ij.intValue() + prod_bv.intValue() + c.intValue(), 2*WBW)  # uv = q2_ij + prod + c

            # set q2[(i+j)*WBW : (i+j+1)*WBW] = uv[0:WBW]
            q2_val = q2.intValue() & (~(((1 << WBW) - 1) << ((i + j) * WBW)))
            q2_val |= (uv.intValue() & ((1 << WBW) - 1)) << ((i + j) * WBW)
            q2 = bv(q2_val, q2_bits)

            # Carry for next limb
            c = bv(uv.intValue() >> WBW, WBW)
        # set q2[(i + n + 1)*WBW : (i + n + 2)*WBW] = c[0:WBW]
        q2_val = q2.intValue() & (~(((1 << WBW) - 1) << ((i + (BITWIDTH + WBW - 1) // WBW + 1) * WBW)))
        q2_val |= (c.intValue() & ((1 << WBW) - 1)) << ((i + (BITWIDTH + WBW - 1) // WBW + 1) * WBW)
        q2 = bv(q2_val, q2_bits)
        print(f"q2 (after column {i}) = {hex(q2.intValue())}") if debug else None
    
    q2_full = bv(q2.intValue(), (3 * LIMBGROUPS + 1) * WBW - BITWIDTH + 1)  # q2_full = bv(q2.intValue(), (2 * LIMBGROUPS + 1) * WBW + 1)
    if debug:
        print(f"q2 = {hex(q2.intValue())}")
        print(f"q2_full = {hex(q2_full.intValue())}")

    # 1. q3 = floor(q2 / b^{k+1})
    q3 = bv(q2_full.intValue() >> (WBW * (LIMBGROUPS + 1)), 2*LIMBGROUPS*WBW-BITWIDTH+1)  # q3 = bv(q2_full.intValue() >> (WBW * (LIMBGROUPS + 1)), 2LIMBGROUPS*WBW+1)
    if debug:
        print(f"q3 = {hex(q3.intValue())}")

    # 2. r1 = x mod b^{k+1}
    r1 = mask_bv(x_full, (LIMBGROUPS + 1) * WBW)
    if debug:
        print(f"r1 = {hex(r1.intValue())}")

    # 2. r2 = (q3 * m) mod b^{k+1}
    # q3m = mul_f_gen(q3, m, q3.size, m.size)
    # 2. r2 = (q3 * m) mod b^{k+1} (WBW-bit multiplier only)
    q3m_bits = 3 * LIMBGROUPS * WBW - BITWIDTH + 1
    q3m = bv(0, q3m_bits)
    for i in range(LIMBGROUPS):
        c = bv(0, WBW)  # carry
        for j in range((BITWIDTH + WBW - 1) // WBW + 1):
            q3_limb = bv((q3.intValue() >> (i * WBW)) & ((1 << WBW) - 1), WBW)
            m_limb = bv((m.intValue() >> (j * WBW)) & ((1 << WBW) - 1), WBW)
            prod_bv = mul_f_WBW(q3_limb, m_limb)

            q3m_ij = bv((q3m.intValue() >> ((i + j) * WBW)) & ((1 << WBW) - 1), WBW)
            uv = bv(q3m_ij.intValue() + prod_bv.intValue() + c.intValue(), 2*WBW)

            # set q3m[(i+j)*WBW : (i+j+1)*WBW] = uv[0:WBW]
            q3m_val = q3m.intValue() & (~(((1 << WBW) - 1) << ((i + j) * WBW)))
            q3m_val |= (uv.intValue() & ((1 << WBW) - 1)) << ((i + j) * WBW)
            q3m = bv(q3m_val, q3m_bits)

            # Carry for next limb
            c = bv(uv.intValue() >> WBW, WBW)
        # set q3m[(i + n + 1)*WBW : (i + n + 2)*WBW] = c[0:WBW]
        q3m_val = q3m.intValue() & (~(((1 << WBW) - 1) << ((i + (BITWIDTH + WBW - 1) // WBW + 1) * WBW)))
        q3m_val |= (c.intValue() & ((1 << WBW) - 1)) << ((i + (BITWIDTH + WBW - 1) // WBW + 1) * WBW)
        q3m = bv(q3m_val, q3m_bits)
        print(f"q3m (after column {i}) = {hex(q3m.intValue())}") if debug else None

    r2 = mask_bv(q3m, (LIMBGROUPS + 1) * WBW)
    if debug:
        print(f"q3m = {hex(q3m.intValue())}")
        print(f"r2 = {hex(r2.intValue())}")

    # 2. r = r1 - r2
    r = bv(r1.intValue() - r2.intValue(), (LIMBGROUPS + 1) * WBW + 1)
    if debug:
        print(f"r (before correction) = {hex(r.intValue())}")
    # r = r.intValue()  # Convert back to int for subsequent arithmetic

    # 3. If r < 0 then r = r + b^{k+1}
    # Check if r is negative by inspecting the MSB
    if (r.intValue() >> (r.size - 1)) & 1:
        r = bv(r.intValue() + (1 << ((LIMBGROUPS + 1) * WBW)), r.size)
        if debug:
            print(f"r (after correction) = {hex(r.intValue())}")

    # 4. While r >= m_full.intValue() do: r = r - m_full
    m_full = bv(m.intValue(), (LIMBGROUPS) * WBW)  # m_full = bv(m.intValue(), BITWIDTH)
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
    if B_REAL & (B_REAL - 1) != 0 or B_REAL == 0:
        raise ValueError(f"B_REAL must be a power of 2, but got {B_REAL}")
    if BITWIDTH & (BITWIDTH - 1) != 0 or BITWIDTH == 0:
        raise ValueError(f"BITWIDTH must be a power of 2, but got {BITWIDTH}")

    dbg = False
    
    m = bv(94638212182620952513693670343372186519186500347741441943556257891053441384207, BITWIDTH)
    mu_val = (B_REAL ** (2 * LIMBGROUPS)) // m.intValue()
    mu = bv(mu_val, 2 * LIMBGROUPS * WBW - BITWIDTH + 1)  # mu = bv(mu_val, BITWIDTH + 1)

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
    mu3_val = B_REAL ** (2 * LIMBGROUPS) // m3_val
    m3 = bv(m3_val, BITWIDTH)
    mu3 = bv(mu3_val, 2 * LIMBGROUPS * WBW - BITWIDTH + 1)  # mu3 = bv(mu3_val, 2*BITWIDTH)
    x3 = bv(21153877054695242909877314665315721334083484317899122095901326116859688255728, BITWIDTH)
    y3 = bv(21153877054695242909877314665315721334083484317899122095901326116859688255728, BITWIDTH)
    result3 = modmul_barrett_core(x3, y3, m3, mu3, dbg)
    print(f"modmul_barrett_core({x3.intValue()}, {y3.intValue()}, {m3.intValue()}, {mu3.intValue()}) = {result3.intValue()}")
    expected3 = (x3.intValue() * y3.intValue()) % m3.intValue()
    print(f"Expected: {expected3}")
    print("Fail" if result3.intValue() != expected3 else "Pass")

    # Additional sample with x and y
    x4 = bv(10576938527347621454938657332657860667041742158949561047950663058429844127864, BITWIDTH)
    y4 = bv(10576938527347621454938657332657860667041742158949561047950663058429844127864, BITWIDTH)
    result4 = modmul_barrett_core(x4, y4, m3, mu3, dbg)
    print(f"modmul_barrett_core({x4.intValue()}, {y4.intValue()}, {m3.intValue()}, {mu3.intValue()}) = {result4.intValue()}")
    expected4 = (x4.intValue() * y4.intValue()) % m3.intValue()
    print(f"Expected: {expected4}")
    print("Fail" if result4.intValue() != expected4 else "Pass")

if __name__ == "__main__":
    main()