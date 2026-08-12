"Reference implementation of modular field operations"

def modadd(a, b, q):
    return (a + b) % q

def modsub(a, b, q):
    return (a - b) % q

def modmul(a, b, q):
    return (a * b) % q

def modsq(a, q):
    return (a * a) % q

def modinv(a, q):
    return pow(a, -1, q)

def get_R(q):
    return 1 << q.bit_length()

def modmul_mont(a, b, q, q_prime):
    "Montgomery modular multiply"
    R = get_R(q)
    t = a * b
    m = (t * q_prime) & (R - 1)
    u = (t + m*q) >> q.bit_length()
    if u >= q:
        u -= q
    return u

def modsq_mont(a, q, q_prime):
    return modmul_mont(a, a, q, q_prime)
