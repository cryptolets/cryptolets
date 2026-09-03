"""
Wrap catapult's makefile so gate level simulation reads the netlist.
"""
from pathlib import Path

import yaml


def gen_gls_makefile(kernel, design_build_dir):
    """
    Write a makefile that simulates the netlist against the same testbench.

    Catapult's own makefile lists two sets of sources: the RTL it wrote, and a
    netlist a synthesis tool produced. Running it with STAGE=gate picks the
    second set, so all that is left to say is where the netlist is and how to
    compile it.

    Compiling a file leaves nothing to check, so catapult marks it done with a
    stamp file standing in for the source. Every source below is named that
    way: the stamp goes in the source list, and the rule under it says which
    file the stamp came from.

    A combinational kernel is synthesized on its own, so only the kernel
    becomes gates and the ports around it stay as RTL. That wrapper is added
    back, since it is what carries the testbench down to the netlist.
    """
    catapult = Path(design_build_dir, "Catapult", f"{kernel}.v1",
                    "scverify", "Verify_rtl_v_msim.mk")
    if not catapult.exists():
        raise Exception(f"No SCVerify makefile at {catapult}, so the RTL was never verified")

    netlist = Path(design_build_dir, "package", "syn", f"{kernel}_gate.v").resolve()
    if not netlist.exists():
        raise Exception(f"No netlist for '{kernel}'. Synthesize it first.\n"
                        f"  expected: {netlist}")

    manifest = yaml.safe_load(Path(design_build_dir, "package", "manifest.yaml").read_text())
    combinational = manifest["combinational"]

    stamp = f"{netlist.name}.vts"
    sources = {stamp: netlist}
    if combinational:
        # Catapult already stamps a cluster as rtl.v, so this one is named for
        # the kernel to keep the two apart
        sources[f"{kernel}_wrapper.v.vts"] = Path(catapult.parent.parent, "rtl.v").resolve()

    # The netlist takes the slot catapult leaves for it, and the wrapper joins
    # the list, which catapult settles as it is read rather than after
    lines = [f"GATE_VLOG_DEP = {netlist.parent}/{stamp}"]
    lines += [f"VLOG_SRC += {src.parent}/{name}"
              for name, src in sources.items() if name != stamp]
    lines.append(f"include {catapult.resolve()}")

    for name, src in sources.items():
        lines += [f"$(TARGET)/{name}: {src}",
                  "\t$(VLOG) -work work $(VLOG_OPTS) $<",
                  "\t@touch $@"]

    makefile = design_build_dir / "gls.mk"
    makefile.write_text("\n".join(lines) + "\n")
    return makefile, combinational
