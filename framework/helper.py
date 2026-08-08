import subprocess
import re
from itertools import product

def get_design_dir_name(design):
    for k, v in design.items():
        if isinstance(v, bool):
            design[k] = int(v)

    return "__".join([f"{k}_{v}" for k, v in design.items()])

def flatten_sweep(sweep):
    keys = list(sweep.keys())
    designs = []

    # Plain params (lists), excluding the n-dependent maps
    plain_keys = [k for k in keys if k not in ('base_mul_width', 'kar_base_mul_width')]
    plain_values = [sweep[k] for k in plain_keys]

    for combo in product(*plain_values):
        design = dict(zip(plain_keys, combo))
        n = design['n']

        bmw_list = sweep.get('base_mul_width', {}).get(n, [None])
        kbmw_list = sweep.get('kar_base_mul_width', {}).get(n, [None])

        for bmw, kbmw in product(bmw_list, kbmw_list):
            d = dict(design)
            if bmw is not None: d['base_mul_width'] = bmw
            if kbmw is not None: d['kar_base_mul_width'] = kbmw
            designs.append(d)

    return designs


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