"""
Custom sweep overrides and filters for kernel-specific behavior.
"""

import json
from pathlib import Path
from naming_short import print_short

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

# Kernels that don't support multi-precision
mp_unsupported_kernels = ["cmul_f", "modsq", "sq_f"]

# --- overrides ---
def config_override(lvl, state, params, order, sweep_bw_maps):    
    # FIELD_A depends on CURVE_TYPE for specifc curves
    if (
        order[lvl-1] == "FIELD_A" 
        and "CURVE_TYPE" in state 
        and state["CURVE_TYPE"] != "RAND_CURVE"
    ):
        params["FIELD_A"] = [CURVE_TO_FIELD_A_MAP.get(state["CURVE_TYPE"], "AVAR")]

    if (
        state.get("PREC_TYPE") == "MULTI_PREC" 
        and "BITWIDTH" in state 
        and order[lvl-1] == "WBW"
    ):
        bw = state.get("BITWIDTH")
        wbw = state.get("WBW")
        new_bw = ((bw + wbw - 1) // wbw) * wbw
        state["BITWIDTH"] = new_bw
        state["MASK_BITS"] = new_bw - bw

    # for when BITWIDTH depends on CURVE_TYPE
    if (
        order[lvl-1] == "CURVE_TYPE" 
        and state["CURVE_TYPE"] != "RAND_CURVE"
    ):
        fp = ROOT_DIR / "field_const.json"
        data = json.load(open(fp))
        curve = state["CURVE_TYPE"]
        if curve in data:
            params["BITWIDTH"] = [data[curve]["bitwidth"]]

    # multi_prec doesn't pipeline so this doesn't matter
    if (
        state.get("PREC_TYPE") == "MULTI_PREC" and
        "TARGET_II" in params
    ):
        params["TARGET_II"] = [1]
    
    # Map overrided based on specific mul types 
    if order[lvl-1] == "BITWIDTH":
        for k in sweep_bw_maps:
            if k in order:
                params[k] = sweep_bw_maps[k][state["BITWIDTH"]]
            
        if state.get("MUL_TYPE") in ("MUL_SCHOOLBOOK", "MUL_NORMAL"):
            params["KAR_BASE_MUL_WIDTH"] = [state["BITWIDTH"]]
        if state.get("MUL_TYPE") == "MUL_NORMAL":
            params["BASE_MUL_WIDTH"] = [state["BITWIDTH"]]

    # --- SWEEP ORDER OVERRIDES ---
    # Remove WBW if precision type is SINGLE_PREC
    if state.get("PREC_TYPE") == "SINGLE_PREC":
        order = [x for x in order if x != "WBW"]

    if state.get("MUL_TYPE") == "MUL_NORMAL":
        order = [x for x in order if x != "KAR_BASE_MUL_WIDTH"]

    return state, params, order


# --- filter logic ---
def override_skip(state, kernel):
    """
    Return True if this complete config should be skipped.
    Similar to early 'if' filters in the Bash sweep function.
    """
    msg = "[WARNING] Skipping - {}:\n  Config Params:" + print_short(state)

    if (
        state.get("CURVE_TYPE") == "RAND_CURVE"
        and state.get("Q_TYPE") == "FIXED_Q"
    ):
        print(msg.format(
            f"Prevents RAND_CURVE with FIXED_Q"
        ))
        return True

    if (
        state.get("CURVE_TYPE") != "RAND_CURVE"
        and state.get("Q_TYPE") == "VAR_Q"
    ):
        print(msg.format(
            f"Prevents specific curves with VAR_Q"
        ))
        return True

    # Skip unsupported MULTI_PREC kernels
    if state.get("PREC_TYPE") == "MULTI_PREC":             
        if str(kernel) in mp_unsupported_kernels:
            print(msg.format(
                f"{str(kernel)} does not support MULTI_PREC"
            ))
            return True

        if state.get("CURVE_TYPE") and state.get("CURVE_TYPE") != "RAND_CURVE":
            print(msg.format(
                f"{state.get('CURVE_TYPE')} does not support MULTI_PREC"
            ))
            return True

    if (
        state.get("KAR_BASE_MUL_WIDTH") is not None
        and state.get("BASE_MUL_WIDTH") is not None
        and state["KAR_BASE_MUL_WIDTH"] < state["BASE_MUL_WIDTH"]
    ):
        return True

    # Add more skip rules as needed ...

    return False