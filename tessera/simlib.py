"""
Compile the vendor models a simulation needs, into questa libraries.
"""
import shutil
import subprocess
from pathlib import Path

# Where questa keeps its executables, below the install it is configured with
BIN_DIR = "linux_x86_64"
# The cells a gate netlist is built from
CELL_LIB = "tech_cells"
# The arithmetic catapult maps a multiply or an add onto
DWARE_LIBS = ["DW01_ver", "DW02_ver", "DW03_ver", "DWARE_ver"]
DWARE_DIR = "dware_cache"


def _run(tool, *args, questa, env, log):
    "Run one questa tool, and fail with its output rather than a return code"
    result = subprocess.run([str(Path(questa, BIN_DIR, tool)), *args], env=env,
                            capture_output=True, text=True)
    log.write(result.stdout + result.stderr)
    if result.returncode:
        raise Exception(f"{tool} failed while compiling the models:\n{result.stdout}")


def build_cells(tech, out_dir, questa, env, log):
    """
    Compile the cell models, and return the modelsim.ini naming them.

    A gate netlist instantiates cells rather than describing what they do, so
    the simulator needs their models.
    """
    lib_dir = (out_dir / CELL_LIB).resolve()
    ini = (out_dir / "modelsim.ini").resolve()

    _run("vlib", str(lib_dir), questa=questa, env=env, log=log)

    # The vendor macros belong to the models, not to the design
    defines = tech.lib_verilog_defines.split()
    _run("vlog", "-work", str(lib_dir), *defines,
         str(Path(tech.lib_verilog).expanduser()), questa=questa, env=env, log=log)

    # vmap edits an ini in place, so it starts from questa's own defaults
    shutil.copyfile(Path(questa, "questa.ini"), ini)
    ini.chmod(0o644)
    _run("vmap", "-ini", str(ini), CELL_LIB, str(lib_dir),
         questa=questa, env=env, log=log)

    return ini


def build_dware(dc, out_dir, mgc_home, questa, env, log):
    """
    Compile the vendor arithmetic, and return the directory holding it.

    Catapult builds these itself for a design it synthesized the arithmetic
    for. A blackboxed dependency arrives as RTL that already names those
    parts, so its parent asks for them here. The list of sources is catapult's
    own, so this drives the makefile that holds it rather than repeating it.
    """
    cache = (out_dir / DWARE_DIR).resolve()
    if (cache / "modelsim.ini").exists():
        return cache

    mkfiles = Path(mgc_home, "shared", "include", "mkfiles")
    drive = out_dir / "dware.mk"
    drive.write_text(
        f"include {mkfiles / 'ccs_default_cmds.mk'}\n"
        f"TARGET = .\n"
        f"SIMTOOL = msim\n"
        f"SIMLIBS_V = {' '.join(DWARE_LIBS)}\n"
        f"SIMLIBS_VHD =\n"
        f"DesignCompiler_Path = {Path(dc).expanduser() / 'bin'}\n"
        f"DesignCompiler_PCL_CACHE = {cache}\n"
        f"QuestaSIM_Path = {Path(questa, BIN_DIR)}\n"
        f"include {mkfiles / 'ccs_DWARE.mk'}\n")

    result = subprocess.run(["make", "-f", str(drive.resolve()),
                         str(cache / "modelsim.ini")],
                            cwd=out_dir, env=env, capture_output=True, text=True)
    log.write(result.stdout + result.stderr)
    if result.returncode:
        raise Exception(f"Could not compile the vendor arithmetic:\n{result.stdout}")

    return cache
