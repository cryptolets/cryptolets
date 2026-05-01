"Reference implementation of elliptic curve points in different coordinates"
import random
from reference.field import modinv

class PointInfinity:
    pass

class PointBase:
    def as_tuple(self):
        return tuple(self.__dict__.values())

    def __repr__(self):
        return str(self.as_tuple())

class PointAffine(PointBase):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
class PointJacobian(PointBase):
    def __init__(self, X=0, Y=0, Z=0):
        self.X = X
        self.Y = Y
        self.Z = Z

class PointExtendedProjective(PointBase):
    def __init__(self, X=0, Y=0, Z=0, T=0):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.T = T
    
class PointExtendedAffine(PointBase):
    def __init__(self, x=0, y=0, u=0):
        self.x = x
        self.y = y
        self.u = u

# Coordinate conversions

def affine_to_jacobian(P: PointAffine, q: int) -> PointJacobian:
    if P is PointInfinity: return PointInfinity

    Z = random.randrange(1, q)  # pick random nonzero Z

    X = (P.x * pow(Z, 2, q)) % q
    Y = (P.y * pow(Z, 3, q)) % q
    return PointJacobian(X, Y, Z)

def jacobian_to_affine(P: PointJacobian, q: int) -> PointAffine:
    if P.Z == 0: return PointInfinity

    Z2 = (P.Z * P.Z) % q
    Z3 = (Z2 * P.Z) % q

    try:
        Z2_inv = modinv(Z2, q)
        Z3_inv = modinv(Z3, q)
    except ValueError:
        return PointInfinity

    x = (P.X * Z2_inv) % q
    y = (P.Y * Z3_inv) % q
    return PointAffine(x, y)

def affine_to_extended_projective(P: PointAffine, q: int) -> PointExtendedProjective:
    if P is PointInfinity: return PointInfinity
    Z = random.randrange(1, q) # pick random nonzero Z
    X = (P.x * Z) % q
    Y = (P.y * Z) % q
    T = (P.x * P.y * Z) % q 
    return PointExtendedProjective(X, Y, Z, T)

def extended_projective_to_affine(P: PointExtendedProjective, q: int) -> PointAffine:
    if P.Z == 0: return PointInfinity

    Z_inv = modinv(P.Z, q)
    x = (P.X * Z_inv) % q
    y = (P.Y * Z_inv) % q

    return PointAffine(x, y)

def affine_to_extended_affine(P: PointAffine, k: int, q: int) -> PointExtendedAffine:
    if P is PointInfinity: return PointInfinity
    u = (P.x * P.y * k) % q
    return PointExtendedAffine(P.x, P.y, u)

def extended_affine_to_affine(P: PointExtendedAffine, q: int) -> PointAffine:
    if P.x == 0 and P.y == 1: return PointInfinity
    return PointAffine(P.x, P.y)