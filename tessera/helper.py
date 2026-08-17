import subprocess
import re
from pathlib import Path

BUILD_DIR = Path('build')

# What a flow writes for a design, and so what a parent reads from a dep it
# blackboxes. A design holding all of a flow's files is built.
PRODUCTS = {
    "catapult": [
        "package/manifest.yaml",   # its ports, area, delay and latency
        "package/{kernel}.v",      # the RTL the blackbox header points at
    ],
    "dc": [
        "package/syn/{kernel}.ddc",   # the synthesized block DC links
    ],
}


def missing_products(kernel, design, flow, build_root=BUILD_DIR):
    "The files a flow should have written for this design, and did not"
    design_dir = Path(build_root, kernel, get_design_dir_name(design, kernel))
    wanted = (design_dir / p.format(kernel=kernel) for p in PRODUCTS[flow])
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

    parts = []
    for key in keys:
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

if __name__ == "__main__":
    print("CatapultUltra_c: ", get_license_info())
    print("Design-Compiler: ", get_license_info("dc"))
    print("PrimePower: ", get_license_info("prime_power"))