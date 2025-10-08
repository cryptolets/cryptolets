# naming_short.py
# Maps sweep parameter keys and values to short and medium forms for filenames.

import yaml
from pathlib import Path

# --- load mappings ---
yaml_file = (Path(__file__).resolve().parent / "../naming_config.yaml").resolve()
with open(yaml_file) as f:
    data = yaml.safe_load(f)

SHORT_KEY = data["SHORT_KEY"]
MED_KEY   = data.get("MED_KEY", {})
VALUE     = data["VALUE"]

# --- reverse maps for decoding ---
R_SHORT_KEY = {v: k for k, v in SHORT_KEY.items()}
R_MED_KEY   = {v: k for k, v in MED_KEY.items()}
R_VALUE     = {k: {v2: v1 for v1, v2 in vs.items()} for k, vs in VALUE.items()}


def short(k, v=None):
    """Return short form for key or key+value."""
    if v is None:
        return SHORT_KEY.get(k, k)
    return VALUE.get(k, {}).get(v, v)


def encoder(config, dot=False):
    """Encode a config dict into a compact, filename-safe string."""
    parts = []
    for k, v in config.items():
        k_short = SHORT_KEY.get(k, k)
        v_short = VALUE.get(k, {}).get(v, str(v))
        if not dot:
            v_short = str(v_short).replace('.', '_')
        parts.append(f"{k_short}_{v_short}")
    return "__".join(parts)


def decoder(tag, key_type="short", val_type="short"):
    """
    Decode a compact tag string back into a config dict.

    key_type options:
      - "short": use SHORT_KEY (default)
      - "med"  : use MED_KEY
      - "full" : use original long-form keys

    val_type options:
      - "short": keep encoded short values (default)
      - "full" : expand to full-form values
    """
    config = {}

    for pair in tag.split("__"):
        if "_" not in pair:
            continue
        k_short, v_short = pair.split("_", 1)

        # --- resolve full key ---
        full_key = (
            R_SHORT_KEY.get(k_short)
            or R_MED_KEY.get(k_short)
            or k_short
        )

        # --- handle value expansion ---
        if val_type == "full":
            val = R_VALUE.get(full_key, {}).get(v_short, v_short)
        else:  # short
            val = v_short

        # --- handle key expansion ---
        if key_type == "full":
            key = full_key
        elif key_type == "med":
            key = (
                MED_KEY.get(full_key)
                or SHORT_KEY.get(full_key)
                or full_key
            )
        else:  # short
            key = (
                SHORT_KEY.get(full_key)
                or MED_KEY.get(full_key)
                or full_key
            )

        config[key] = val

    return config