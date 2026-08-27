import os
import re
import signal
import subprocess
import uuid
import time
import logging
from pathlib import Path

from tessera.const import BUILD_DIR, DONE_DIR


def free_gb():
    "Memory the machine can still hand out, cache it would reclaim included"
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024**2
    return float("inf")


def watch_memory(stop, min_free_gb):
    "Stop every tool, and this run, when the machine is nearly out of memory"
    while not stop.wait(5):
        if free_gb() < min_free_gb:
            logging.error(f"Less than {min_free_gb}G of memory left, "
                          f"stopping every tool")
            os.killpg(os.getpgid(0), signal.SIGTERM)
            return

# A stage that finished leaves its mark in DONE_DIR, so a later run knows not
# to repeat it. A stage that failed leaves nothing.
def _done_dir(kernel, design, build_root):
    return Path(build_root, kernel, get_design_dir_name(design, kernel), DONE_DIR)


def mark_done(kernel, design, stage, build_root=BUILD_DIR):
    "Record that a stage finished for this design"
    done = _done_dir(kernel, design, build_root)
    done.mkdir(parents=True, exist_ok=True)
    (done / f"{stage}.done").touch()


def is_done(kernel, design, stage, build_root=BUILD_DIR):
    "Whether a stage has already finished for this design"
    return (_done_dir(kernel, design, build_root) / f"{stage}.done").exists()


def require_built(kernel, design, stage, build_root=BUILD_DIR):
    "Fail unless the stage a later one reads from has finished"
    if not is_done(kernel, design, stage, build_root):
        raise Exception(
            f"'{kernel}' at bitwidth {design['bitwidth']} period {design['period']} "
            f"has no {stage} results, so build it with that flow first.")


def get_design_dir_name(design, kernel=None):
    """
    What a design's build directory is called.

    The kernel names the parameters that change its hardware, so two designs
    differing only in one it ignores are the same build. Without a kernel the
    whole design names it, which is what the sweep itself is keyed on.
    """
    keys = list(design)
    if kernel:
        from tessera.models import KernelConfig
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