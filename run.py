#!/usr/bin/env python3
import yaml, subprocess, argparse, sys
from pathlib import Path

def run_cmd(cmd):
    print(f"[RUN] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print("\n[ERROR] Command failed")
        print(f"Command   : {' '.join(cmd)}")
        print(f"Exit code : {e.returncode}")
        sys.exit(e.returncode)


def invert(mapping: dict) -> dict:
    """Invert group -> kernels map into kernel -> group."""
    inv = {}
    for group, kernels in mapping.items():
        for k in kernels:
            if k in inv:
                raise ValueError(f"Kernel '{k}' appears in multiple groups.")
            inv[k] = group
    return inv


def main():
    parser = argparse.ArgumentParser(description="Run sweep generation for a specific kernel.")
    parser.add_argument("kernel", help="Target kernel name (e.g., mul_f).")
    parser.add_argument("--threads", type=int, help="Override total thread count.")
    parser.add_argument("--tp", type=int, help="Override threads per process.")
    parser.add_argument("--rtl", type=str, help="Override RTL mode (rtl or rtl_concat).")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulate run without executing.")
    parser.add_argument("--gui", dest="gui_mode", action="store_true", help="Enable GUI mode (if supported).")
    parser.add_argument("--gen-only", action="store_true",
                        help="Generate sweep JSON only (skip parallel run).")
    parser.add_argument("--run-only", action="store_true",
                        help="Run Catapult parallel only (requires existing tmp JSON).")

    args = parser.parse_args()

    # --- load configuration ---
    cfg = yaml.safe_load(open("run_config.yaml"))

    kernels      = cfg["KERNELS"]
    sweep_groups = cfg["SWEEP_GROUP_MAP"]
    core_groups  = cfg["CORE_GROUP_MAP"]

    total_threads = args.threads or cfg.get("TOTAL_THREADS", 1)
    threads_per   = args.tp or cfg.get("THREADS_PER_PROCESS", 1)
    rtl_mode      = args.rtl or cfg.get("RTL_FILE", "rtl")

    # --- handle dry-run and gui defaults properly ---
    dry_run  = cfg.get("DRY_RUN", False)
    gui_mode = cfg.get("GUI_MODE", False)

    # CLI flags override config defaults if present
    if args.dry_run:
        dry_run = True
    if args.gui_mode:
        gui_mode = True

    # --- validation ---
    k = args.kernel
    if k not in kernels:
        raise ValueError(f"Kernel '{k}' not found in KERNELS list.")

    sweep_map = invert(sweep_groups)
    core_map  = invert(core_groups)

    if k not in sweep_map or k not in core_map:
        raise KeyError(f"Kernel '{k}' missing from SWEEP_GROUP_MAP or CORE_GROUP_MAP.")

    # --- prepare paths ---
    pgrp = sweep_map[k]
    cgrp = core_map[k]
    sweep_file = f"{pgrp}_sweep.yaml"
    out_file = f"tmp_configs/{k}_configs.json"
    core_script = f"tcl_cores/catapult_{cgrp}_core.tcl"
    
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)

    # --- handle run modes ---
    if args.run_only and not Path(out_file).exists():
        raise FileNotFoundError(
            f"[ERROR] Cannot run parallel — missing config file: {out_file}. "
            "Run with --gen-only or default mode first."
        )

    # --- run sweep generation ---
    if not args.run_only:
        cmd = [
            "python3", "utils/generate_sweep.py",
            "--sweep", sweep_file,
            "--out", out_file,
            "--kernel", k
        ]
        run_cmd(cmd)
        if args.gen_only:
            print(f"[INFO] Generated {out_file}, skipping parallel execution (--gen-only).")
            return  # Exit after sweep generation

    # --- run parallel ---
    cmd = [
        "./run_catapult_parallel.sh",
        core_script,        # CORE_CATAPULT_SCRIPT
        k,                  # KERNEL_NAME
        out_file,           # CONFIG_FILE
        str(total_threads), # TOTAL_THREADS
        str(threads_per),   # THREADS_PER_PROCESS
        rtl_mode,           # RTL_FILE
    ]
    if dry_run:
        cmd.append("--dry-run")
    if gui_mode:
        cmd.append("--gui")

    run_cmd(cmd)

    # --- Idea: multi-kernel batch mode (not implemented) ---
    # TODO:
    #   - Add support for multi-kernel execution using MULTIPLE_KERNELS list
    #   - Run selected kernels in parallel with subprocess.Popen
    #   - Control concurrency using TOTAL_THREADS and THREADS_PER_PROCESS
    #   - Optionally merge outputs into a combined JSON


if __name__ == "__main__":
    main()