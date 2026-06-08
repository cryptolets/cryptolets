from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
FIELD_JSON = "field_const.json"

# Configs
FIELD_CONTS = [
    "a", "b", "k", "d",
]

SUPPORTED_A_ASSUMPTIONS = {
    "Weierstrass": [0, 2, -3], # Short Weierstrass
    "TwistedEdwards": [-1] # Twisted Edwards
}

# Helpers Functions
def fa_to_str(a, q, curve_form):
    if curve_form in SUPPORTED_A_ASSUMPTIONS:
        for a_int in SUPPORTED_A_ASSUMPTIONS[curve_form]:
            if (a_int % q) == a:
                return f"ANEG{abs(a_int)}" if a_int < 0 else f"A{a_int}"
    return "AVAR"

def fa_to_int(a):
    if a == "AVAR":
        return 5
    elif "NEG" in a:
        return -int(a.replace("ANEG", ""))
    else:
        return int(a[1:])

def to_hex(n):
    return hex(n)[2:]

field_data = json.load(open(ROOT_DIR / FIELD_JSON))
CURVE_TO_FIELD_A_MAP = {}

for curve in field_data:
    CURVE_TO_FIELD_A_MAP[curve] = fa_to_str(
            int(field_data[curve]["a"], 16),
            int(field_data[curve]["q"], 16),
            field_data[curve]["form"]
        )

def compute_naf(n):
    if n == 0: return [0]
    naf = []
    while n > 0:
        if n & 1:
            z = 2 - (n % 4)
            naf.append(z)
            n = n - z
        else:
            naf.append(0)
        n = n >> 1
    return naf