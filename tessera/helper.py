import subprocess
import re
import uuid
import time
import logging
from pathlib import Path

BUILD_DIR = Path('build')

# What a stage writes for a design, and so what a parent reads from a dep it
# blackboxes. A design holding all of a stage's files is built.
PRODUCTS = {
    "gen": [
        "include/params.h",
        "include/{kernel}_top.h",
        "src/{kernel}_top.cpp",
        "design.tcl",
        "test/samples.csv",   # only written when the c++ test runs
    ],
    "hls": [
        "package/manifest.yaml",   # its ports, area, delay and latency
        "package/{kernel}.v",      # the RTL the blackbox header points at
    ],
    "syn": [
        "package/syn/{kernel}.ddc",   # the synthesized block DC links
    ],
}

# A stage naming no product leaves nothing to reuse, so it always runs
ALWAYS_RUNS = object()


def missing_products(kernel, design, stage, build_root=BUILD_DIR):
    "The files a stage should have written for this design, and did not"
    if stage not in PRODUCTS:
        return [ALWAYS_RUNS]

    design_dir = Path(build_root, kernel, get_design_dir_name(design, kernel))
    wanted = (design_dir / p.format(kernel=kernel) for p in PRODUCTS[stage])
    return [p for p in wanted if not p.exists()]


def require_built(kernel, design, flow, build_root=BUILD_DIR):
    "Fail unless the flow has written everything a later one reads"
    missing = missing_products(kernel, design, flow, build_root)
    if missing:
        raise Exception(
            f"'{kernel}' at bitwidth {design['bitwidth']} period {design['period']} "
            f"has no {flow} results, so build it with that flow first.\n"
            + "\n".join(f"  missing: {p}" for p in missing))

def get_design_dir_name(design, kernel=None):
    """
    What a design's build directory is called.

    The kernel names the parameters that change its hardware, so two designs
    differing only in one it ignores are the same build. Without a kernel the
    whole design names it, which is what the sweep itself is keyed on.
    """
    keys = list(design)
    if kernel:
        from tessera.config import KernelConfig
        from tessera.kernel import find_kernel
        keys = KernelConfig.load(find_kernel(kernel)).design_key or keys

    # A parameter the sweep did not give this design names nothing, so a
    # multiplier that never splits carries no base width
    parts = []
    for key in keys:
        if key not in design:
            continue
        value = design[key]
        parts.append(f"{key}_{int(value) if isinstance(value, bool) else value}")
    return "__".join(parts)

def tcl_type(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        return f'"{value}"'
    return value


PRODUCT_TO_LMSTAT_NAME = {
    "catapult_ultra": "CatapultUltra_c:",
    "dc": "Design-Compiler:",
    "prime_power": "PrimePower:",
}

def get_license_info(product="catapult_ultra"):
    "returns num of licenses available and in use."
    result = subprocess.run(
        f"lmstat -a | grep -i {PRODUCT_TO_LMSTAT_NAME[product]}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
        check=True,
    )

    out = result.stdout
    m = re.search(r"Total of (\d+).*issued.*Total of (\d+).*in use", out)
    if not m: return None
    issued = int(m.group(1))
    in_use = int(m.group(2))
    return {"issued": issued, "in_use": in_use, "available": issued - in_use}


def log_elapsed(tool, design_name, return_code, start_time):
    elapsed = time.time() - start_time
    hrs, mins, secs = int(elapsed // 3600), int((elapsed % 3600) // 60), elapsed % 60
    status = "COMPLETED" if return_code == 0 else "FAILED"
    log = logging.info if return_code == 0 else logging.error
    log(f"{tool} {status} for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")
    return return_code == 0


# ---- archive design helper functions ----
KEEP = ("prior", "ccore_cache", "dware_cache") # these don't get archived

def _move(design_build_dir, names, label):
    if not names:
        return

    run_dir = design_build_dir / "prior" / f"run_{label}{uuid.uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (design_build_dir / name).rename(run_dir / name)


def archive_run(design_build_dir, label="", dirs=("Catapult", "dc")):
    "Move a finished run's tool directories aside, so the next one starts clean"
    if "Catapult" in dirs:
        dirs = (*dirs, "Catapult.ccs")

    _move(design_build_dir, [d for d in dirs if (design_build_dir / d).exists()],
          label)


def archive_design(design_build_dir, label=""):
    "Move a whole finished run aside, the sources it was built from included"
    _move(design_build_dir,
          [p.name for p in design_build_dir.iterdir() if p.name not in KEEP],
          label)