"""
Helper functions to patch catapult's makefile for gate level simulation.
"""
import re
from pathlib import Path

import yaml

# Catapult names the slot holding the design under test
DUT_SLOT = "$(TARGET)/rtl.v.vts"
CELL_SLOT = "$(TARGET)/cells.v.vts"


def patch(mk, pattern, replacement, what, count=0):
    "Edit the makefile, and fail if it does not look the way we expect"
    patched, made = re.subn(pattern, replacement, mk, count=count)
    if not made:
        raise Exception(f"Gate level simulation cannot {what}: no match for {pattern!r}")
    return patched


def gen_gls_makefile(kernel, design_build_dir, gls_dir, lib_verilog, lib_defines=""):
    """
    Patch catapult's makefile so it simulates the gate netlist.

    Catapult already wrote one that simulates the RTL against the testbench,
    listing every source SCVerify compiles. Gate level simulation reuses it,
    so the same testbench and the same goldens check the netlist.

    Three things change:
    1. The design under test becomes Design Compiler's 
       netlist rather than Catapult's RTL. 
    2. Any RTL the netlist already holds is dropped, 
       since verilog keeps the last definition it reads and the
       behavioural version would win. 
    3. The standard cell models are added, 
       since the netlist instantiates cells the RTL never did.
    """
    src = Path(design_build_dir, "Catapult", f"{kernel}.v1",
               "scverify", "Verify_rtl_v_msim.mk")
    if not src.exists():
        raise Exception(f"No SCVerify makefile at {src}, so the RTL was never verified")

    manifest = yaml.safe_load(Path(design_build_dir, "package", "manifest.yaml").read_text())
    netlist = Path(design_build_dir, "package", "syn", f"{kernel}_gate.v").resolve()
    mk = src.read_text()

    # The netlist already holds this dep, so we drop it.
    if re.search(r"\.\./\.\./blackbox/\S+\.vts", mk):
        mk = patch(mk, r"\.\./\.\./blackbox/(\w+)\.v/\1\.v\.vts ?", "",
                   "drop the blackboxed dependencies")

    # And its clusters (cluster refers to the catapult feature)
    if re.search(r"ccore_cache/\S+\.vts", mk):
        mk = patch(mk, r"\S*ccore_cache/\S+?\.vts ?", "", "drop the cluster RTL")

        # A sequential design arrives in a slot of its own
        mk = patch(mk, r"\./rtl\.v/rtl\.v_\d+\.vts", DUT_SLOT, "find the sequential design")

    # Simulate the netlist rather than the RTL. The slot appears again to
    # carry per file options, so this matches the line naming a source.
    mk = patch(mk, rf"{re.escape(DUT_SLOT)}: (?![A-Z_]+=)\S+", f"{DUT_SLOT}: {netlist}",
               "find the design under test")

    # The cell models, in front of the wrapper that ends the source list
    mk = patch(mk, r"(\./scverify/ccs_wrapper\.v/ccs_wrapper\.v\.vts)",
               lambda m: f"{CELL_SLOT} {m[1]}", "add the cell models to the sources")

    # Where those cell models are read from
    mk = patch(mk, r"(\$\(TARGET\)/ccs_wrapper\.v\.vts: \./scverify/ccs_wrapper\.v)",
               f"{CELL_SLOT}: {lib_verilog}\n" + r"\1",
               "give the cell models a source file", count=1)

    # And how the cell models compile. ARM needs its unknown squash, or the cells hold
    # X and the first transaction reads as a wrong answer.
    mk = patch(mk, rf"({re.escape(DUT_SLOT)}: HDL_LIB=)",
               f"{CELL_SLOT}: HDL_LIB=work\n"
               f"{CELL_SLOT}: VLOG_F_OPTS={lib_defines}\n" + r"\1",
               "compile the cell models")

    gls_dir.mkdir(parents=True, exist_ok=True)
    makefile = design_build_dir / "gls.mk"
    makefile.write_text(mk)
    return makefile, manifest["combinational"]
