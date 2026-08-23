"""
Compile the technology cells the gate netlist is built from.
"""
import shutil
import subprocess
from pathlib import Path

# The library the cells are compiled into, which the netlist links against
CELL_LIB = "tech_cells"
# Where questa keeps its executables, below the install it is configured with
BIN_DIR = "linux_x86_64"


def _run(tool, *args, questa, env, log):
    "Run one questa tool, and fail with its output rather than a return code"
    result = subprocess.run([str(Path(questa, BIN_DIR, tool)), *args], env=env,
                            capture_output=True, text=True)
    log.write(result.stdout + result.stderr)
    if result.returncode:
        raise Exception(f"{tool} failed while compiling the cells:\n{result.stdout}")


def build_cell_lib(tech, gls_dir, questa, env, log):
    """
    Compile the cell models, and return the modelsim.ini naming them.

    A gate netlist instantiates cells rather than describing what they do, so
    the simulator needs their models. Compiling them up front lets the netlist
    link against them by name.
    """
    # Simulation runs from the catapult solution, so the paths it reads back
    # cannot be relative to here
    lib_dir = (gls_dir / CELL_LIB).resolve()
    ini = (gls_dir / "modelsim.ini").resolve()

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
