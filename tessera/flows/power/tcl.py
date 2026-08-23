"""
Measure power with PrimePower, from the activity recorded in GLS.
"""
import re
import yaml
from pathlib import Path

from tessera.config import RunConfig
from tessera.templating import render

def gen_power_tcl(design, kernel, design_build_dir, power_dir, max_cores):
    "Write the PrimePower script for one design"
    conf = RunConfig.load()
    tech = conf.tech[design["tech_type"]]

    package_dir = design_build_dir / "package"
    manifest = yaml.safe_load(Path(package_dir, "manifest.yaml").read_text())

    vcd = design_build_dir / "gls" / "gate.vcd"
    if not vcd.exists():
        raise Exception(
            f"No switching activity for '{kernel}'. Build it with gls enabled "
            f"first.\n  expected: {vcd}")

    # Where the design sits in the recording, which packaging worked out
    dut_path = manifest["dut_path"]
    sdc = Path(package_dir, manifest["sdc"])

    power_dir.mkdir(parents=True, exist_ok=True)
    render(
        "power.tcl.j2",
        design_build_dir / "power.tcl",
        entity=manifest["entity"],
        netlist=str(Path(package_dir, "syn", f"{kernel}_gate.v").resolve()),
        sdc=str(sdc.resolve()),
        vcd=str(vcd.resolve()),
        dut_path=dut_path,
        clock=real_clock(sdc),
        target_library=str(Path(tech.lib_db).expanduser()),
        max_cores=max_cores,
    )


def real_clock(sdc):
    """
    The clock the design runs on, or nothing when it has none.

    A combinational design is given a virtual clock to constrain its ports
    against, and power cannot be attributed to the cycles of one.
    """
    for name, ports in re.findall(r"create_clock\s+-name\s+(\S+).*?(\[get_ports[^\]]*\])?\s*$",
                                  sdc.read_text(), re.M):
        if ports:
            return name
    return None


# An unannotated net is read as never switching, so a design the simulation
# barely covered still reports a number, and it is too low
MIN_ANNOTATED = 90.0


def read_power(power_dir):
    "Parse the PrimePower's power report"
    annotation = Path(power_dir, "annotation.rpt")
    annotated = re.search(r"^\s*Nets\s+\d+\(([\d.]+)%\)", annotation.read_text(), re.M)
    if not annotated or float(annotated.group(1)) < MIN_ANNOTATED:
        raise Exception(f"Too little of the design was simulated to measure its "
                        f"power.\n  see: {annotation}")

    report = Path(power_dir, "power.rpt")
    if not report.exists():
        raise Exception(f"PrimePower wrote no report at {report}")

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
