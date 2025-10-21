from sympy import randprime, sqrt_mod, mod_inverse, Integer
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

def get_q_prime(q, bitwidth):
    R = Integer(1) << bitwidth
    return (-mod_inverse(q, R)) % R

def get_mu(q, bitwidth):
    R = Integer(1) << bitwidth
    return (Integer(1) << (2 * bitwidth)) // q 

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


class TwistedEdwards:
    def __init__(self, q, a, d):
        self.q = q
        self.a = a % q
        self.d = d % q

    def is_on_curve(self, P: EC_point_A):
        """Check affine point lies on TE curve: ax² + y² = 1 + dx²y²."""
        x, y = P.x % self.q, P.y % self.q
        lhs = (self.a * x * x + y * y) % self.q
        rhs = (1 + self.d * x * x * y * y) % self.q
        return lhs == rhs

    def random_point(self):
        """Generate random affine point on curve."""
        while True:
            x = random.randrange(1, self.q)
            # Solve for y² = (1 - ax²) / (1 - dx²)
            num = (1 - self.a * x * x) % self.q
            den = (1 - self.d * x * x) % self.q
            if den == 0:
                continue
            try:
                den_inv = mod_inverse(den, self.q)
            except ValueError:
                continue
            rhs = (num * den_inv) % self.q
            roots = sqrt_mod(rhs, self.q, all_roots=True)
            if roots:
                return EC_point_A(x, roots[0] % self.q)

    def add(self, P: EC_point_A, Q: EC_point_A):
        """Affine addition formula for Twisted Edwards."""
        if P is None: return Q
        if Q is None: return P
        x1, y1 = P.x, P.y
        x2, y2 = Q.x, Q.y

        den_x = (1 + self.d * x1 * x2 * y1 * y2) % self.q
        den_y = (1 - self.d * x1 * x2 * y1 * y2) % self.q
        if den_x == 0 or den_y == 0:
            return None

        try:
            den_x_inv = mod_inverse(den_x, self.q)
            den_y_inv = mod_inverse(den_y, self.q)
        except ValueError:
            return None

        x3 = ((x1 * y2 + y1 * x2) * den_x_inv) % self.q
        y3 = ((y1 * y2 - self.a * x1 * x2) * den_y_inv) % self.q
        return EC_point_A(x3, y3)

    def aff_to_ep(self, P: EC_point_A):
        if P is None:
            return EC_point_EP(0, 1, 1, 0)
        x, y = P.x % self.q, P.y % self.q
        Z = random.randrange(1, self.q)
        X = (x * Z) % self.q
        Y = (y * Z) % self.q
        T = (x * y * Z) % self.q 
        return EC_point_EP(X, Y, Z, T)

    def ep_to_aff(self, P: EC_point_EP):
        if P.Z == 0:
            return None
        Z_inv = mod_inverse(P.Z, self.q)
        x = (P.X * Z_inv) % self.q
        y = (P.Y * Z_inv) % self.q
        # optional: sanity check
        assert (P.T * Z_inv) % self.q == (x * y) % self.q
        return EC_point_A(x, y)