"""
Measure power with PrimeTime, from the activity a gate level simulation recorded.

Design Compiler estimates power by assuming how often a net switches. Here every
net carries the activity it had while the testbench ran, so the report also holds
what a static estimate cannot give: peak power, and the power lost to glitches.
"""
import re
from pathlib import Path

import yaml

from tessera.config import RunConfig
from tessera.templating import render

# Where SCVerify puts the design under test, relative to its testbench
DUT_INST = "scverify_top/rtl/dut_inst"

# A combinational kernel is a CCORE inside a wrapper, so the wrapper is the
# instance SCVerify drives and the kernel itself sits one level below it
CCORE_INST = "core_run_cmp"


def gen_power_tcl(design, kernel, design_build_dir, power_dir, max_cores):
    "Write the PrimeTime script for one design"
    conf = RunConfig.load()
    tech = conf.tech[design["tech_type"]]

    package_dir = design_build_dir / "package"
    manifest = yaml.safe_load(Path(package_dir, "manifest.yaml").read_text())

    vcd = design_build_dir / "gls" / "gate.vcd"
    if not vcd.exists():
        raise Exception(
            f"No switching activity for '{kernel}'. Build it with gls enabled "
            f"first.\n  expected: {vcd}")

    dut_path = f"{DUT_INST}/{CCORE_INST}" if manifest["combinational"] else DUT_INST

    power_dir.mkdir(parents=True, exist_ok=True)
    render(
        "power.tcl.j2",
        power_dir / "power.tcl",
        entity=manifest["entity"],
        netlist=str(Path(package_dir, "syn", f"{kernel}_gate.v").resolve()),
        sdc=str(Path(package_dir, manifest["sdc"]).resolve()),
        vcd=str(vcd.resolve()),
        dut_path=dut_path,
        target_library=str(Path(tech.lib_db).expanduser()),
        max_cores=max_cores,
    )


def read_power(power_dir):
    """
    The design's power, as {switching, internal, leakage, total, peak}, in watts.

    PrimeTime reports a summary at the end of the run, one figure per line.
    """
    report = Path(power_dir, "power.rpt")
    if not report.exists():
        raise Exception(f"PrimeTime wrote no report at {report}")

    fields = {
        "switching": r"Net Switching Power\s+=\s+(\S+)",
        "internal": r"Cell Internal Power\s+=\s+(\S+)",
        "leakage": r"Cell Leakage Power\s+=\s+(\S+)",
        "total": r"Total Power\s+=\s+(\S+)",
        "peak": r"Peak Power\s+=\s+(\S+)",
    }

    text = report.read_text()
    power = {}
    for name, pattern in fields.items():
        match = re.search(pattern, text)
        if match:
            power[name] = float(match.group(1))

    if "total" not in power:
        raise Exception(f"No total power in {report}, so the analysis did not finish")

    return power
