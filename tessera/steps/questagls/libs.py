"""
Compile the vendor models a simulation needed for QuestaSim
"""
import os
import subprocess
from pathlib import Path

from tessera.const import CELLS_DIR, DWARE_DIR
from tessera.models.config import RunConfig

# Where questa keeps its executables, below the install it is configured with
BIN_DIR = "linux_x86_64"
DWARE_LIBS = ["DW01_ver", "DW02_ver", "DW03_ver", "DWARE_ver"]

def build_dware(dc, mgc_home, questa, log):
    """
    Compile the DesignWare simulation models, once, for Catapult's RTL verify.

    Catapult compiles models only for the units it mapped in the current run.
    A blackboxed child's RTL was mapped in a different run, so its parts are
    missing from the parent's RTL simulation. 
    This builds the whole set instead, from Catapult's own makefile for it.
    """
    if (DWARE_DIR / "modelsim.ini").exists():
        return DWARE_DIR
    DWARE_DIR.mkdir(parents=True, exist_ok=True)

    mkfiles = Path(mgc_home, "shared", "include", "mkfiles")
    dware_mk = DWARE_DIR / "dware.mk"
    dware_mk.write_text(
        f"include {mkfiles / 'ccs_default_cmds.mk'}\n"
        f"TARGET = .\n"
        f"SIMTOOL = msim\n"
        f"SIMLIBS_V = {' '.join(DWARE_LIBS)}\n"
        f"SIMLIBS_VHD =\n"
        f"DesignCompiler_Path = {Path(dc).expanduser() / 'bin'}\n"
        f"DesignCompiler_PCL_CACHE = {DWARE_DIR}\n"
        f"QuestaSIM_Path = {Path(questa, BIN_DIR)}\n"
        f"include {mkfiles / 'ccs_DWARE.mk'}\n")

    result = subprocess.run(
        ["make", "-f", str(dware_mk), str(DWARE_DIR / "modelsim.ini")],
        cwd=DWARE_DIR, stdout=log, stderr=subprocess.STDOUT
    )

    if result.returncode:
        raise Exception(f"Could not compile the DesignWare models, see {log.name}")
    return DWARE_DIR


def questa_env():
    """
    Where questa is installed, and the environment its tools run in
    """
    questa = str(Path(RunConfig.load().tools["questa"]).expanduser())
    env = {
        **os.environ,
        # Questa reads its own license variable
        "SALT_LICENSE_SERVER": os.environ.get("MGLS_LICENSE_FILE", ""),
        "QSIM_HOME": questa,
    }
    return questa, env


def _run(tool, *args, questa, env, log):
    """
    Helper func to run questa tool
    """
    result = subprocess.run(
        [str(Path(questa, BIN_DIR, tool)), *args], 
        env=env, capture_output=True, text=True
    )

    log.write(result.stdout + result.stderr)
    if result.returncode:
        raise Exception(f"{tool} failed while compiling the models:\n{result.stdout}")


# The arithmetic catapult maps a multiply or an add onto
CELL_LIB = "tech_cells" # The cells a gate netlist is built from

def build_cells(tech_type, tech, questa, env, log):
    """
    Compile the tech's cell models into a Questa library, once per tech, and
    return the modelsim.ini. A gate netlist instantiates cells
    (e.g. NAND, DFF) by name, so gate level simulation needs their simulation models.
    """
    out_dir = CELLS_DIR / tech_type
    ini = out_dir / "modelsim.ini"
    if ini.exists():
        return ini
    out_dir.mkdir(parents=True, exist_ok=True)
    lib_dir = out_dir / CELL_LIB

    _run("vlib", str(lib_dir), questa=questa, env=env, log=log)

    # The vendor macros belong to the models, not to the design
    defines = tech.lib_verilog_defines.split()
    _run(
        "vlog", "-work", str(lib_dir), *defines, str(Path(tech.lib_verilog).expanduser()), 
        questa=questa, env=env, log=log
    )

    ini.write_text(Path(questa, "questa.ini").read_text())
    _run(
        "vmap", "-ini", str(ini), CELL_LIB, str(lib_dir), 
        questa=questa, env=env, log=log
    )

    return ini