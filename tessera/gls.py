"""
Gate-Level Simulation (GLS): 
   Run the RTL testbench against the synthesized netlist.

Catapult generates a makefile listing the Verilog that SCVerify compiles. 
For gate level simulation, we reuse all of it and swap one entry: 
the design under test becomes the netlist Design Compiler produced.
"""
import os
import re
import subprocess
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
    Write the makefile that simulates the netlist, and return its path.

    The dependency line for the design's slot names Catapult's RTL, so pointing
    it at the DC netlist makes it work for gate level simulation. 
    For a combinational kernel we use the CCORE's netlist, so the wrapper around it stays RTL.
    """
    src = Path(design_build_dir, "Catapult", f"{kernel}.v1",
               "scverify", "Verify_rtl_v_msim.mk")
    if not src.exists():
        raise Exception(f"No SCVerify makefile at {src}, so the RTL was never verified")

    manifest = yaml.safe_load(Path(design_build_dir, "package", "manifest.yaml").read_text())
    netlist = Path(design_build_dir, "package", "syn", f"{kernel}_gate.v").resolve()
    mk = src.read_text()

    # A blackboxed dep was synthesized into the netlist, so its RTL would be a
    # second definition of the same module
    if re.search(r"\.\./\.\./blackbox/\S+\.vts", mk):
        mk = patch(mk, r"\.\./\.\./blackbox/(\w+)\.v/\1\.v\.vts ?", "",
                   "drop the blackboxed dependencies")

    # The netlist defines the design and its clusters as gates, so Catapult's
    # own RTL for them would be a second definition
    if re.search(r"ccore_cache/\S+\.vts", mk):
        mk = patch(mk, r"\S*ccore_cache/\S+?\.vts ?", "", "drop the cluster RTL")
        mk = patch(mk, r"\./rtl\.v/rtl\.v_\d+\.vts", DUT_SLOT, "find the sequential design")

    # The slot appears again to carry per file options, so match the line that
    # names a source rather than one that sets a variable
    mk = patch(mk, rf"{re.escape(DUT_SLOT)}: (?![A-Z_]+=)\S+", f"{DUT_SLOT}: {netlist}",
               "find the design under test")

    # The netlist instantiates cells, so their models are compiled alongside it.
    # The wrapper is the last source, so the models go in front of it.
    mk = patch(mk, r"(\./scverify/ccs_wrapper\.v/ccs_wrapper\.v\.vts)",
               lambda m: f"{CELL_SLOT} {m[1]}", "add the cell models to the sources")
    mk = patch(mk, r"(\$\(TARGET\)/ccs_wrapper\.v\.vts: \./scverify/ccs_wrapper\.v)",
               f"{CELL_SLOT}: {lib_verilog}\n" + r"\1",
               "give the cell models a source file", count=1)
    mk = patch(mk, rf"({re.escape(DUT_SLOT)}: HDL_LIB=)",
               f"{CELL_SLOT}: HDL_LIB=work\n"
               f"{CELL_SLOT}: VLOG_F_OPTS={lib_defines}\n" + r"\1",
               "compile the cell models")

    gls_dir.mkdir(parents=True, exist_ok=True)
    makefile = design_build_dir / "gls.mk"
    makefile.write_text(mk)
    return makefile, manifest["combinational"]


def run_gls(kernel, design_build_dir, gls_dir, makefile, questa_home):
    """
    Simulate the netlist, and return whether it matched the golden outputs.
    """
    env = {
        **os.environ,
        # Questa reads its own license variable, which the Catapult flow sets for us
        "SALT_LICENSE_SERVER": os.environ.get("MGLS_LICENSE_FILE", ""),
        "QSIM_HOME": str(Path(questa_home).expanduser()),
    }

    # TARGET is where the compiled libraries land. Overriding it keeps them out
    # of the Catapult project, so a run always compiles the netlist it was given.
    solution = Path(design_build_dir, "Catapult", f"{kernel}.v1")
    target = os.path.relpath(gls_dir.resolve(), solution.resolve())

    log_path = design_build_dir / "gls.tessera.log"
    with log_path.open("w") as log:
        subprocess.run(
            ["make", "-f", str(makefile.resolve()), "SIMTOOL=msim", f"TARGET={target}",
             f"CCS_VCD_FILE={(gls_dir / 'gate.vcd').resolve()}", "sim"],
            cwd=solution,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    # SCVerify reports the comparison itself, and make exits 0 either way
    return "Simulation PASSED" in log_path.read_text()
