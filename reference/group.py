"Reference implementation of elliptic curve group operations"
from sympy import sqrt_mod
import random

from reference.field import modinv
from reference.coordinates import PointAffine, PointInfinity

class ShortWeierstrass:
    "Short Weierstrass curve: y^2 = x^3 + ax + b"
    def __init__(self, q, a, b):
        self.q = q
        self.a = a % q
        self.b = b % q

    def is_on_curve(self, P: PointAffine):
        "Check affine point lies on curve."
        x, y = P.x, P.y
        return (y*y - (x*x*x + self.a*x + self.b)) % self.q == 0

    def random_point(self) -> PointAffine:
        "Generate random affine point on curve."
        while True:
            x = random.randrange(1, self.q)
            rhs = (x**3 + self.a*x + self.b) % self.q
            roots = sqrt_mod(rhs, self.q, all_roots=True)
            if roots:
                return PointAffine(x % self.q, roots[0] % self.q)

    def add(self, P: PointAffine, Q: PointAffine) -> PointAffine:
        "Affine point addition."
        if P is PointInfinity: return Q
        if Q is PointInfinity: return P
        x1, y1 = P.x, P.y
        x2, y2 = Q.x, Q.y
        if x1 == x2 and (y1 + y2) % self.q == 0:
            return PointInfinity

        if x1 != x2:
            lam = ((y2 - y1) * modinv(x2 - x1, self.q)) % self.q
        else:  # doubling
            lam = ((3 * x1 * x1 + self.a) * modinv(2 * y1, self.q)) % self.q

        x3 = (lam*lam - x1 - x2) % self.q
        y3 = (lam*(x1 - x3) - y1) % self.q
        return PointAffine(x3, y3)


class TwistedEdwards:
    "Twisted Edwards curve: ax^2 + y^2 = 1 + dx^2y^2"
    def __init__(self, q, a, d):
        self.q = q
        self.a = a % q
        self.d = d % q
        self.k = (2 * d) % q

    def is_on_curve(self, P: PointAffine):
        "Check affine point lies on curve"
        x, y = P.x % self.q, P.y % self.q
        lhs = (self.a * x * x + y * y) % self.q
        rhs = (1 + self.d * x * x * y * y) % self.q
        return lhs == rhs

    def random_point(self) -> PointAffine:
        "Generate random affine point on curve."
        while True:
            x = random.randrange(1, self.q)
            # Solve for y² = (1 - ax²) / (1 - dx²)
            num = (1 - self.a * x * x) % self.q
            den = (1 - self.d * x * x) % self.q
            if den == 0:
                continue
            try:
                den_inv = modinv(den, self.q)
            except ValueError:
                continue
            rhs = (num * den_inv) % self.q
            roots = sqrt_mod(rhs, self.q, all_roots=True)
            if roots:
                return PointAffine(x, roots[0] % self.q)

    def add(self, P: PointAffine, Q: PointAffine) -> PointAffine:
        "Affine point addition."
        if P is PointInfinity: return Q
        if Q is PointInfinity: return P
        x1, y1 = P.x, P.y
        x2, y2 = Q.x, Q.y

        den_x = (1 + self.d * x1 * x2 * y1 * y2) % self.q
        den_y = (1 - self.d * x1 * x2 * y1 * y2) % self.q
        if den_x == 0 or den_y == 0:
            return PointInfinity

        try:
            den_x_inv = modinv(den_x, self.q)
            den_y_inv = modinv(den_y, self.q)
        except ValueError:
            return PointInfinity

        x3 = ((x1 * y2 + y1 * x2) * den_x_inv) % self.q
        y3 = ((y1 * y2 - self.a * x1 * x2) * den_y_inv) % self.q
        return PointAffine(x3, y3)