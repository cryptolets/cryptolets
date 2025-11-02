#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.field_helpers import (
    modadd, modsub, modmul, moddouble, EC_point_EP
)

def point_add_te_ref(P0, P1, q, a, d, k):
    result = EC_point_EP()

    if a == (-1 % q):
        t0       = modsub(P0.Y, P0.X, q) # t0 = Y1-X1
        t1       = modsub(P1.Y, P1.X, q) # t1 = Y2-X2
        A        = modmul(t0, t1, q)     # A = t0*t1
        t2       = modadd(P0.Y, P0.X, q) # t2 = Y1+X1
        t3       = modadd(P1.Y, P1.X, q) # t3 = Y2+X2
        B        = modmul(t2, t3, q)     # B = t2*t3
        t4       = modmul(k, P1.T, q)    # t4 = k*T2
        C        = modmul(P0.T, t4, q)   # C = T1*t4
        t5       = moddouble(P1.Z, q)    # t5 = 2*Z2
        D        = modmul(P0.Z, t5, q)   # D = Z1*t5
        E        = modsub(B, A, q)       # E = B-A
        F        = modsub(D, C, q)       # F = D-C
        G        = modadd(D, C, q)       # G = D+C
        H        = modadd(B, A, q)       # H = B+A
        result.X = modmul(E, F, q)       # X3 = E*F
        result.Y = modmul(G, H, q)       # Y3 = G*H
        result.T = modmul(E, H, q)       # T3 = E*H
        result.Z = modmul(F, G, q)       # Z3 = F*G
    else:
        A        = modmul(P0.X, P1.X, q) # A = X1*X2
        B        = modmul(P0.Y, P1.Y, q) # B = Y1*Y2
        t0       = modmul(d, P1.T, q)    # t0 = d*T2
        C        = modmul(P0.T, t0, q)   # C = T1*t0
        D        = modmul(P0.Z, P1.Z, q) # D = Z1*Z2
        t1       = modadd(P0.X, P0.Y, q) # t1 = X1+Y1
        t2       = modadd(P1.X, P1.Y, q) # t2 = X2+Y2
        t3       = modmul(t1, t2, q)     # t3 = t1*t2
        t4       = modsub(t3, A, q)      # t4 = t3-A
        E        = modsub(t4, B, q)      # E = t4-B
        F        = modsub(D, C, q)       # F = D-C
        G        = modadd(D, C, q)       # G = D+C
        t5       = modmul(a, A, q)       # t5 = a*A
        H        = modsub(B, t5, q)      # H = B-t5
        result.X = modmul(E, F, q)       # X3 = E*F
        result.Y = modmul(G, H, q)       # Y3 = G*H
        result.T = modmul(E, H, q)       # T3 = E*H
        result.Z = modmul(F, G, q)       # Z3 = F*G
    return result
