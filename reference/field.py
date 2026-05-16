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

# Montgomery Domain
def to_mont(x, q):
    "Convert scalar or tuple to Montgomery domain."
    from reference.coordinates import PointBase
    R = get_R(q)
    if isinstance(x, PointBase):
        return type(x)(*[(xi * R) % q for xi in x.as_tuple()])
    return (x * R) % q

def from_mont(x, q):
    "Convert scalar or tuple back from Montgomery domain."
    from reference.coordinates import PointBase
    R = get_R(q)
    R_inv = modinv(R, q)
    if isinstance(x, PointBase):
        return type(x)(*[(xi * R_inv) % q for xi in x.as_tuple()])
    return (x * R_inv) % q

def mont_get_q_prime(q):
    R = get_R(q)
    return (-modinv(q, R)) % R

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

# Barrett Domain
def barrett_get_mu(q):
    return (1 << (2 * q.bit_length())) // q 