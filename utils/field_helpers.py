from sympy import randprime, sqrt_mod, mod_inverse
from pathlib import Path
import random
import sys
import json

# points
class ECPointBase:
    def as_tuple(self):
        return tuple(self.__dict__.values())

    def __repr__(self):
        return str(self.as_tuple())

class EC_point_A(ECPointBase):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
class EC_point_J(ECPointBase):
    def __init__(self, X=0, Y=0, Z=0):
        self.X = X
        self.Y = Y
        self.Z = Z

class EC_point_EP(ECPointBase):
    def __init__(self, X=0, Y=0, Z=0, T=0):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.T = T
    
class EC_point_EA(ECPointBase):
    def __init__(self, x=0, y=0, u=0):
        self.x = x
        self.y = y
        self.u = u

# functions
def get_field_const(curve_type, const_name, json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        if const_name == "bitwidth":
            return int(data[curve_type][const_name])
        return int(data[curve_type][const_name], 16) # convert from hex to int

# Mont conversions
def to_mont(x, q):
    """Convert scalar or tuple to Montgomery domain."""
    R = 1 << q.bit_length()
    if isinstance(x, tuple):
        return tuple((xi * R) % q for xi in x)
    return (x * R) % q

def from_mont(x, q):
    """Convert scalar or tuple back from Montgomery domain."""
    R = 1 << q.bit_length()
    R_inv = mod_inverse(R, q)
    if isinstance(x, tuple):
        return tuple((xi * R_inv) % q for xi in x)
    return (x * R_inv) % q

# mod ops
def modadd(a, b, q):
    return (a + b) % q

def moddouble(a, q):
    return (a + a) % q

def modsub(a, b, q):
    return (a - b) % q

def modsq(a, q):
    return (a * a) % q

def modmul(a, b, q):
    return (a * b) % q

def modmul_mont(a, b, q, q_prime, Rbits):
    """Full Montgomery multiply: (a*b*R^-1) mod q, Mont in -> Mont out."""
    R = 1 << Rbits
    t = a * b
    m = (t * q_prime) & (R - 1)   # low Rbits
    u = (t + m*q) >> Rbits
    if u >= q:
        u -= q
    return u

def modsq_mont(a, q, q_prime, Rbits):
    return modmul_mont(a, q, q_prime, Rbits)


class ShortWeierstrass:
    def __init__(self, q, a, b):
        self.q = q
        self.a = a % q
        self.b = b % q

    def is_on_curve(self, P: EC_point_A):
        """Check affine point lies on curve."""
        x, y = P.x, P.y
        return (y*y - (x*x*x + self.a*x + self.b)) % self.q == 0

    def random_point(self):
        """Generate random affine point on curve."""
        while True:
            x = random.randrange(1, self.q)
            rhs = (x**3 + self.a*x + self.b) % self.q
            roots = sqrt_mod(rhs, self.q, all_roots=True)
            if roots:
                return EC_point_A(x % self.q, roots[0] % self.q)

    def add(self, P: EC_point_A, Q: EC_point_A):
        """Affine addition. Returns EC_point_A or None for infinity."""
        if P is None: return Q
        if Q is None: return P
        x1, y1 = P.x, P.y
        x2, y2 = Q.x, Q.y
        if x1 == x2 and (y1 + y2) % self.q == 0:
            return None  # point at infinity

        if x1 != x2:
            lam = ((y2 - y1) * mod_inverse(x2 - x1, self.q)) % self.q
        else:  # doubling
            lam = ((3 * x1 * x1 + self.a) * mod_inverse(2 * y1, self.q)) % self.q

        x3 = (lam*lam - x1 - x2) % self.q
        y3 = (lam*(x1 - x3) - y1) % self.q
        return EC_point_A(x3, y3)

    def aff_to_jac(self, P: EC_point_A):
        """Convert affine (x, y) to Jacobian (X, Y, Z) with random Z != 0."""
        if P is None:
            return EC_point_J(1, 1, 0)  # infinity

        x, y = P.x % self.q, P.y % self.q
        Z = random.randrange(1, self.q)  # pick random nonzero Z

        X = (x * pow(Z, 2, self.q)) % self.q
        Y = (y * pow(Z, 3, self.q)) % self.q
        return EC_point_J(X, Y, Z)

    def jac_to_aff(self, Pj: EC_point_J):
        """Convert Jacobian to affine (EC_point_A)."""
        X, Y, Z = Pj.X, Pj.Y, Pj.Z
        if Z == 0:
            return None  # point at infinity

        Z2 = (Z * Z) % self.q
        Z3 = (Z2 * Z) % self.q

        try:
            Z2_inv = mod_inverse(Z2, self.q)
            Z3_inv = mod_inverse(Z3, self.q)
        except ValueError:
            return None  # no inverse, treat as infinity

        x = (X * Z2_inv) % self.q
        y = (Y * Z3_inv) % self.q
        return EC_point_A(x, y)