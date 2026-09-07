"License checks, so a pool is capped by what is free"
import re
import subprocess


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
