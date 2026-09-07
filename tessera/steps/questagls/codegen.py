"""
Generate makefile for Gate Level Simulation
"""
from pathlib import Path
import yaml


def gen_gls_makefile(design, kernel):
    """
    Write a makefile that runs Catapult's testbench against the DC netlist.

    It wraps Catapult's own SCVerify makefile rather than replacing it: the
    netlist is put in the gate slot, and a combinational kernel gets its
    clocked wrapper back as RTL, since DC synthesized only the CCORE inside it.
    """

    # catapult's makefile as the base
    catapult = design.build_dir / "Catapult" / f"{kernel.name}.v1" / "scverify" / "Verify_rtl_v_msim.mk"
    if not catapult.exists():
        raise Exception(f"No SCVerify makefile at {catapult}, so the RTL was never verified")

    netlist = (design.build_dir / "package" / "syn" / f"{kernel.name}_gate.v").resolve()
    manifest = yaml.safe_load((design.build_dir / "package" / "manifest.yaml").read_text())
    combinational = manifest["combinational"]

    stamp = f"{netlist.name}.vts"
    sources = {stamp: netlist}
    if combinational:
        sources[f"{kernel.name}_wrapper.v.vts"] = Path(catapult.parent.parent, "rtl.v").resolve()

    lines = [] # lines for new wrapper makefile
    lines.append(f"GATE_VLOG_DEP = {netlist.parent}/{stamp}") # point to netlist
    for name, src in sources.items():
        if name != stamp: # the netlist is already in the list, as GATE_VLOG_DEP
            lines.append(f"VLOG_SRC += {src.parent}/{name}")
    lines.append(f"include {catapult.resolve()}") # include catapult's makefile

    # For combinational kernels Catapult lists the CCORE's RTL
    # We want to make sure we are using the netlist, not the CCORE's RTL
    # The below lines skip the CCORE's RTL from being compiled
    if combinational: 
        lines.append("$(TARGET)/rtl.v.vts:")
        lines.append("\t@touch $@")

    for name, src in sources.items():
        lines.append(f"$(TARGET)/{name}: {src}")
        lines.append("\t$(VLOG) -work work $(VLOG_OPTS) $<")
        lines.append("\t@touch $@")

    makefile = design.build_dir / "gls.mk"
    makefile.write_text("\n".join(lines) + "\n")
    return makefile, combinational
