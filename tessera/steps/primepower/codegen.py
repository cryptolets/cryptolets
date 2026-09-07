"""
Measure power with PrimePower, from the activity recorded in GLS.
"""
import yaml
from pathlib import Path

from tessera.models.config import RunConfig
from tessera.templating import render

def gen_power_tcl(design, kernel, run_inst):
    """
    Write the PrimePower tcl script
    """
    tech = RunConfig.load().tech[design.design["tech_type"]]

    package_dir = design.build_dir / "package"
    manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text())
    sdc = package_dir / "syn" / f"{kernel.name}_gate.sdc"

    power_dir = design.build_dir / "power"
    power_dir.mkdir(parents=True, exist_ok=True)
    render(
        "power.tcl.j2",
        design.build_dir / "power.tcl",
        module=manifest["module"],
        netlist=str((package_dir / "syn" / f"{kernel.name}_gate.v").resolve()),
        sdc=str(sdc.resolve()),
        vcd=str((design.build_dir / "gls" / "gate.vcd").resolve()),
        dut_path=manifest["dut_path"],
        clock=None if manifest["combinational"] else "clk",
        target_library=str(Path(tech.lib_db).expanduser()),
        max_cores=run_inst.threads_per_process,
    )
