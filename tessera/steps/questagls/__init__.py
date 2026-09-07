import logging
import os
import subprocess
import time
from pathlib import Path

from tessera.models.config import RunConfig
from tessera.steps.base import Step
from tessera.steps.questagls.libs import CELL_LIB, build_cells, questa_env
from tessera.const import CELLS_DIR
from tessera.steps.questagls.codegen import gen_gls_makefile
from tessera.steps.catapult.package import update_manifest
from tessera.helper import archive_run, log_elapsed


class QuestaSimGLS(Step):
    """
    Gate-Level Simulation (GLS): 
        Run the RTL testbench against the synthesized netlist.

    Catapult generates a makefile listing the Verilog that SCVerify compiles. 
    For gate level simulation, we reuse all of it and swap one entry: 
    the design under test becomes the netlist Design Compiler produced.
    """
    name = "gls"

    def setup(self, kernel, designs, run_inst):
        conf = RunConfig.load()
        questa, env = questa_env()

        for tech_type in sorted({d.design["tech_type"] for d in designs}):
            tech = conf.tech[tech_type]
            if not tech.lib_verilog:
                raise Exception(f"'{tech_type}' has no lib_verilog, so its cells "
                                f"cannot be simulated")
            log_path = CELLS_DIR / tech_type / "cells.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as log:
                build_cells(tech_type, tech, questa, env, log)

    @staticmethod
    def run_sim(makefile, design, kernel, log):
        gls_dir = design.build_dir / "gls"
        cells_dir = CELLS_DIR / design.design["tech_type"]

        # Questa reads the ini naming the cell models through its own variable
        questa, env = questa_env()
        env["MODELSIM"] = str(cells_dir / "modelsim.ini")

        solution_dir = design.build_dir / "Catapult" / f"{kernel.name}.v1"
        target_dir = os.path.relpath(gls_dir.resolve(), solution_dir.resolve())

        subprocess.run(
            ["make", "-f", str(makefile.resolve()), "SIMTOOL=msim",
             f"TARGET={target_dir}",
             "STAGE=gate", # The gate stage reads the netlist rather than the RTL, and an
             "RTLTOOL=", # blank because we already ran Design Compiler
             f"ADDED_VLOGLIBS={cells_dir / CELL_LIB}",
             "SIMLIBS_V=", # blank because gate level netlist doesn't need designware simulation models
             f"CCS_VCD_FILE={(gls_dir / 'gate.vcd').resolve()}", "sim"],
            cwd=solution_dir,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    def run(self, design, kernel, run_inst):
        design_name = design.build_dir.name
        start_time = time.time()

        archive_run(design.build_dir, dirs=("gls",))
        (design.build_dir / "gls").mkdir(parents=True, exist_ok=True)

        # Generate the makefile that will be used to run the simulation
        # This uses Catapult's makefile, and builds a new gls.mk wrapper makefile
        makefile, combinational = gen_gls_makefile(design, kernel)
        logging.info(
            f"Running QuestaSim GLS for {design_name} "
            f"({'combinational' if combinational else 'sequential'})"
        )

        log_path = design.build_dir / "logs" / "gls.tessera.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w") as log:
            self.run_sim(makefile, design, kernel, log)

        # Check log to see if the simulation passed
        # because SCVerify returns exit code 0 even if the simulation fails
        passed = "Simulation PASSED" in log_path.read_text()
        update_manifest(design, gls=passed)
        return log_elapsed(self.name, design_name, 0 if passed else 1, start_time)
