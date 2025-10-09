#!/usr/bin/env python3
import yaml, json, argparse
from pathlib import Path
from custom_sweep_overrides import \
    config_override, override_skip

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
    sweep_bw_maps = {}
    for k in SWEEP_BITWIDTH_ARRAY_MAPS:
        if sweep.get(k):
            sweep_bw_maps[k] = sweep.get(k, {})

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

    return order, params, flags, sweep_bw_maps


def expand(order, params, kernel, sweep_bw_maps, lvl=0, state=None):
    if state is None:
        state = {}
    
    # for debugging
    # print("  "*lvl, "state", state)

    state, params, order = config_override(lvl, state, params, order, sweep_bw_maps)

    if lvl == len(order):
        if override_skip(state, kernel):
            return []
        return [state]

    cur = order[lvl]
    out = []

    for v in params[cur]:
        s = state.copy()
        s[cur] = v
        out.extend(expand(order.copy(), params.copy(), kernel, sweep_bw_maps, lvl + 1, s))
    
    # for debugging
    # print("  "*lvl, "out", out)
    return out

def main():
    p = argparse.ArgumentParser(description="Generate flattened sweep configs from YAML.")
    p.add_argument("--kernel", required=True, type=Path)
    p.add_argument("--sweep", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--verbose", action="store_true", help="Print all generated configurations.")
    a = p.parse_args()

    sweep = load_yaml(a.sweep)
    order, params, flags, sweep_bw_maps = validate(sweep)
    configs = expand(order, params, a.kernel, sweep_bw_maps)

    with open(a.out, "w") as f:
        json.dump({"control_flags": flags, "sweep_configs": configs}, f, indent=2)

    print("===========================================")
    print("Generated Sweep Configurations")
    print("===========================================")
    if a.verbose:
        print("-------------------------------------------")
        for i, cfg in enumerate(configs):
            cfg_str = ", ".join(f"{k}={v}" for k, v in cfg.items())
            print(f"[{i+1:03d}] {cfg_str}")
        print("-------------------------------------------")
    print(f"TOTAL CONFIGS: {len(configs)}")
    print(f"JSON Output: {a.out}")
    print("[OK] Sweep generation complete.")

if __name__ == "__main__":
    main()
