import logging
import subprocess
import time
from pathlib import Path

from tessera.models.kernel import KernelConfig
from tessera.steps.base import Step
from tessera.steps.package.write import update_manifest
from tessera.steps.dc.reports import read_dc_area, read_dc_delay, read_dc_power
from tessera.steps.dc.select import select_designs
from tessera.steps.dc.tcl import gen_dc_tcl
from tessera.helper import archive_run, get_design_dir_name, log_elapsed


class DesignCompiler(Step):
    """
    Logic synthesis using Design Compiler. RTL to a Gate netlist.
    """
    name = "syn"
    license = "dc"

    def designs(self, designs, kernel_ctx):
        # Synthesis costs far more than the run that estimated it, so a sweep
        # can ask for only the designs on its frontier
        kernel_key = KernelConfig.load(kernel_ctx.kernel_path).kernel_key
        return select_designs(designs, kernel_ctx.kernel, kernel_ctx.kernel_build_dir,
                              kernel_ctx.sweep_flags["syn_sel"], kernel_key)

    def run(self, design, kernel_ctx):
        design_name = get_design_dir_name(design, kernel_ctx.kernel)
        design_build_dir = Path(kernel_ctx.kernel_build_dir, design_name)
        start_time = time.time()

        # Generate the Design Compiler TCL script
        entity = gen_dc_tcl(design, kernel_ctx.kernel, kernel_ctx.impl_spec,
                            kernel_ctx.kernel_path, design_build_dir,
                            kernel_ctx.threads_per_process)

        logging.info(f"Running Design Compiler for {design_name}")

        # Design Compiler writes its work directories into the current one, so
        # it gets its own. Catapult's is left alone for a syn only run.
        archive_run(design_build_dir, dirs=("dc",))
        dc_dir = design_build_dir / "dc"
        dc_dir.mkdir(parents=True, exist_ok=True)

        log_path = design_build_dir / "logs" / "dc.tessera.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w") as log:
            result = subprocess.run(
                ["dc_shell", "-f", str((design_build_dir / "dc.tcl").resolve())],
                cwd=dc_dir,
                stdout=log,
                stderr=subprocess.STDOUT,
            )

        ok = log_elapsed(self.name, design_name, result.returncode, start_time)
        if ok:
            measured = {"area_dc": read_dc_area(design_build_dir),
                        "delay_dc": read_dc_delay(design_build_dir),
                        "power_dc": read_dc_power(design_build_dir, entity)}
            update_manifest(design_build_dir,
                            **{k: v for k, v in measured.items() if v})
        return ok
