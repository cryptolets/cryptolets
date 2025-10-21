from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
FIELD_JSON = "field_const.json"

# Configs
FIELD_CONTS = [
    "a", "b", "k", "d",
]

# Short Weierstrass
SUPPORTED_A_ASSUMPTIONS_SW = [
    0, 2, -3
]

# Twisted Edwards
SUPPORTED_A_ASSUMPTIONS_TE = [
    -1
]

# Helpers Functions
def fa_to_str(a, q, curve_form):
    sw_a_to_mod_map = {(a % q): a_int for a_int in SUPPORTED_A_ASSUMPTIONS_SW}
    te_a_to_mod_map = {(a % q): a_int for a_int in SUPPORTED_A_ASSUMPTIONS_TE}

    if (
        (curve_form == "Weierstrass" and a in sw_a_to_mod_map) or 
        (curve_form == "TwistedEdwards" and a in te_a_to_mod_map)
    ):
        a_int = sw_a_to_mod_map[a] if curve_form == "Weierstrass" else \
                te_a_to_mod_map[a]

        if a_int < 0: # negative
            return f"ANEG{abs(a_int)}"
        else:
            return f"A{a_int}"

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