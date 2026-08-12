"Montgomery and Barrett domain helpers, shared across modular kernels"
from reference.field import modinv, get_R

def mont_get_q_prime(q):
    R = get_R(q)
    return (-modinv(q, R)) % R

def to_mont(x, q):
    "Convert scalar or point to Montgomery domain."
    from reference.coordinates import PointBase
    R = get_R(q)
    if isinstance(x, PointBase):
        return type(x)(*[(xi * R) % q for xi in x.as_tuple()])
    return (x * R) % q

def from_mont(x, q):
    "Convert scalar or point back from Montgomery domain."
    from reference.coordinates import PointBase
    R = get_R(q)
    R_inv = modinv(R, q)
    if isinstance(x, PointBase):
        return type(x)(*[(xi * R_inv) % q for xi in x.as_tuple()])
    return (x * R_inv) % q

def barrett_get_mu(q):
    return (1 << (2 * q.bit_length())) // q
