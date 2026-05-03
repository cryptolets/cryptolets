import subprocess
import re
from itertools import product

def get_design_dir_name(design):
    for k, v in design.items():
        if isinstance(v, bool):
            design[k] = int(v)

    return "__".join([f"{k}_{v}" for k, v in design.items()])

def flatten_sweep(sweep):
    # TODO: We need to way to filter/override the sweep
    keys = list(sweep.keys())
    values = list(sweep.values())
    return [dict(zip(keys, combo)) for combo in product(*values)]


def unflatten_sweep(flattened_sweep):
    sweep_config = {}
    for design in flattened_sweep:
        for k, v in design.items():
            if k not in sweep_config:
                sweep_config[k] = []
            if v not in sweep_config[k]:
                sweep_config[k].append(v)
    return sweep_config


def tcl_type(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        return f'"{value}"'
    return value


def get_catapult_license_info(product="CatapultUltra_c"):
    "returns num of licenses available and in use."
    result = subprocess.run(
        f"lmstat -a | grep -i {product}",
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