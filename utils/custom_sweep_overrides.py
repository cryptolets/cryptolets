"""
Custom sweep overrides and filters for kernel-specific behavior.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

CURVE_TO_FIELD_A_MAP = {
    "BN254": "A0",
    "BLS12_377": "A0",
    "BLS12_381": "A0",
    "SECP256K1": "A0",
    "P_256": "ANEG3",
    "P_521": "ANEG3",
    "MNT4753": "A2",
    "BLS12_377_ED": "ANEG1",
    "MNT4753_ED": "ANEG1",
    "ED25519": "ANEG1",
    "ED_384_MONT": "ANEG1",
    "ED_511_MERS": "ANEG1",
    "ED_512_MONT": "ANEG1",
    "ED448": "AVAR",
}

# --- value overrides ---
def override_values(name, state, values):
    """
    Called before expanding each parameter.
    Modify 'values' based on partial state, or return unchanged list.
    """
    # Example: FIELD_A depends on CURVE_TYPE
    if name == "FIELD_A" and "CURVE_TYPE" in state:
        if state["CURVE_TYPE"] != "RAND_CURVE":
            return [CURVE_TO_FIELD_A_MAP.get(state["CURVE_TYPE"], "AVAR")]

    # BITWIDTH depends on CURVE_TYPE
    if name == "BITWIDTH" and "CURVE_TYPE" in state:
        if state["CURVE_TYPE"] != "RAND_CURVE":
            fp = ROOT_DIR / "field_const.json"
            data = json.load(open(fp))
            curve = state["CURVE_TYPE"]
            if curve in data:
                return [data[curve]["bitwidth"]]

    # KAR_BASE_MUL_WIDTH override
    if name == "KAR_BASE_MUL_WIDTH" and "MUL_TYPE" in state:
        bw = state.get("BITWIDTH")
        if state["MUL_TYPE"] in ("MUL_SCHOOLBOOK", "MUL_NORMAL") and bw:
            return [bw]

    # BASE_MUL_WIDTH override
    if name == "BASE_MUL_WIDTH" and state.get("MUL_TYPE") == "MUL_NORMAL":
        bw = state.get("BITWIDTH")
        if bw:
            return [bw]

    return values


# --- filter logic ---
def override_skip(state, kernel):
    """
    Return True if this complete config should be skipped.
    Similar to early 'if' filters in the Bash sweep function.
    """
    # if (
    #     state.get("CURVE_TYPE") == "RAND_CURVE"
    #     and state.get("Q_TYPE") == "FIXED_Q"
    # ):
    #     return True

    # if (
    #     state.get("CURVE_TYPE") != "RAND_CURVE"
    #     and state.get("Q_TYPE") == "VAR_Q"
    # ):
    #     return True

    # Skip unsupported MULTI_PREC kernels
    unsupported_multi = [
        "cmul_f", "modsq", "sq_f"
    ]
    if (
        state.get("PREC_TYPE") == "MULTI_PREC"
        and str(kernel) in unsupported_multi
    ):  
        return True

    if (
        state.get("KAR_MUL_DEPTH") is not None
        and state.get("BASE_MUL_DEPTH") is not None
        and state["KAR_MUL_DEPTH"] < state["BASE_MUL_DEPTH"]
    ):
        return True

    # Add more skip rules as needed
    return False

def override_sweep_order(order, base):
    # Remove LIMBS if precision type is SINGLE_PREC
    if "PREC_TYPE" in base and base["PREC_TYPE"] == "SINGLE_PREC":
        order = [x for x in order if x != "LIMBS"]

    return order