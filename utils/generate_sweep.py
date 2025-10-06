#!/usr/bin/env python3
import yaml, json, argparse
from pathlib import Path
from custom_sweep_overrides import \
    override_values, override_skip, override_sweep_order

SWEEP_BITWIDTH_ARRAY_MAPS = ["BASE_MUL_WIDTH", "KAR_BASE_MUL_WIDTH"]

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def validate(sweep):
    if "SWEEP_ORDER" not in sweep:
        raise KeyError("SWEEP_ORDER missing.")
    order = sweep["SWEEP_ORDER"]
    if not isinstance(order, list) or not order:
        raise ValueError("SWEEP_ORDER must be a non-empty list.")

    # --- extract maps explicitly ---
    bm_map = sweep.get("BASE_MUL_WIDTH", {})
    kar_map  = sweep.get("KAR_BASE_MUL_WIDTH", {})

    # --- classify sweep entries ---
    params = {
        k: v for k, v in sweep.items()
        if isinstance(v, list)
        and k not in ("SWEEP_ORDER") 
        and k not in SWEEP_BITWIDTH_ARRAY_MAPS
    }
    flags = {
        k: v for k, v in sweep.items()
        if not isinstance(v, (list, dict))
        and k != "SWEEP_ORDER"
    }

    # --- validation (ignore maps) ---
    missing = [
        k for k in order
        if k not in params
        and k not in SWEEP_BITWIDTH_ARRAY_MAPS
    ]
    extra = [k for k in params if k not in order]

    if missing:
        raise KeyError(f"Missing parameters in sweep: {missing}")
    if extra:
        print(f"[WARNING] extra parameters not in SWEEP_ORDER -> {extra}")

    return order, params, flags, bm_map, kar_map


def expand(order, params, kernel, bm_map, kar_map, lvl=0, base=None):
    if base is None:
        base = {}
    if lvl == len(order):
        if override_skip(base, kernel):
            return []
        return [base]

    key = order[lvl]

    if key == "BASE_MUL_WIDTH":
        params[key] = bm_map[base["BITWIDTH"]]
    if key == "KAR_BASE_MUL_WIDTH":
        params[key] = kar_map[base["BITWIDTH"]]
        
    order = override_sweep_order(order, base)
    vals = override_values(key, base, params[key])

    out = []
    for v in vals:
        b = base.copy()
        b[key] = v
        out.extend(expand(order, params, kernel, bm_map, kar_map, lvl + 1, b))
    return out

def main():
    p = argparse.ArgumentParser(description="Generate flattened sweep configs from YAML.")
    p.add_argument("--kernel", required=True, type=Path)
    p.add_argument("--sweep", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--verbose", action="store_true", help="Print all generated configurations.")
    a = p.parse_args()

    sweep = load_yaml(a.sweep)
    order, params, flags, bm_map, kar_map = validate(sweep)
    configs = expand(order, params, a.kernel, bm_map, kar_map)

    with open(a.out, "w") as f:
        json.dump({"control_flags": flags, "sweep_configs": configs}, f, indent=2)

    print("===========================================")
    print("Generated Sweep Configurations")
    print("===========================================")
    print(f"TOTAL CONFIGS: {len(configs)}")
    print(f"JSON Output: {a.out}")
    if a.verbose:
        print("-------------------------------------------")
        for i, cfg in enumerate(configs):
            cfg_str = ", ".join(f"{k}={v}" for k, v in cfg.items())
            print(f"[{i+1:03d}] {cfg_str}")
        print("-------------------------------------------")
    print("[OK] Sweep generation complete.")

if __name__ == "__main__":
    main()
