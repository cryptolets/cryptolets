# naming_short.py
# Maps sweep parameter keys and values to short forms for file and directory names.

PARAM = {
    "BITWIDTH": "bw",
    "TARGET_II": "ii",
    "TARGET_PERIOD": "p",
    "MUL_TYPE": "mt",
    "Q_TYPE": "qt",
    "KAR_BASE_MUL_WIDTH": "kar",
    "BASE_MUL_WIDTH": "bm",
    "TECH_TYPE": "tt",
    "CURVE_TYPE": "ct",
    "FIELD_A": "fa",
    "PREC_TYPE": "pt",
    "LIMBS": "l"
}

VALUE = {
    "MUL_TYPE": {
        "MUL_NORMAL": "nor",
        "MUL_KARATSUBA": "kar",
        "MUL_SCHOOLBOOK": "sb"
    },
    "Q_TYPE": {
        "FIXED_Q": "fixedq",
        "VAR_Q": "varq"
    },
    "FIELD_A": {
        "AVAR": "var",
        "AN1": "n1",
        "AN3": "n3",
        "A0": "0"
    },
    "PREC_TYPE": {
        "SINGLE_PREC": "sp",
        "MULTI_PREC": "mp"
    }
}

# --- reverse maps for decoding ---
R_PARAM = {v: k for k, v in PARAM.items()}
R_VALUE = {k: {v2: v1 for v1, v2 in vs.items()} for k, vs in VALUE.items()}

def short(k, v=None):
    """Return short form for key or key+value."""
    if v is None:
        return PARAM.get(k, k)
    return VALUE.get(k, {}).get(v, v)

def encoder(config, dot=False):
    """Encode a config dict into a compact, filename-safe string."""
    parts = []
    for k, v in config.items():
        k_short = PARAM.get(k, k)
        v_short = VALUE.get(k, {}).get(v, str(v))
        if not dot:
            v_short = str(v_short).replace('.', '_')
        parts.append(f"{k_short}_{v_short}")
    return "__".join(parts)

def decoder(tag, full=False):
    """
    Decode a compact tag string back into a config dict.
    By default returns short-form keys/values.
    Set full=True to return expanded (full-form) keys and values.
    """
    config = {}
    for pair in tag.split("__"):
        if "_" not in pair:
            continue
        k_short, v_short = pair.split("_", 1)

        if full:
            # expand both key and value
            key = R_PARAM.get(k_short, k_short)
            val = None
            if key in R_VALUE and v_short in R_VALUE[key]:
                val = R_VALUE[key][v_short]
            else:
                val = v_short
        else:
            # return as-is (short forms)
            key = k_short
            val = v_short

        config[key] = val
    return config