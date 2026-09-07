import logging
import subprocess
import time
from pathlib import Path

from tessera.models.config import RunConfig
from tessera.steps.base import Step
from tessera.steps.package.write import update_manifest
from tessera.steps.primepower.tcl import gen_power_tcl, read_power
from tessera.helper import (archive_run, get_design_dir_name, is_done,
                            log_elapsed)


class PrimePower(Step):
    "Measure power from the activity a gate level simulation recorded"
    name = "pwr"
    license = "prime_power"

    def designs(self, designs, kernel_ctx):
        "A gate simulation that did not pass recorded no activity to measure"
        return [d for d in designs if is_done(kernel_ctx.kernel, d, "gls")]

    def run(self, design, kernel_ctx):
        design_name = get_design_dir_name(design, kernel_ctx.kernel)
        design_build_dir = Path(kernel_ctx.kernel_build_dir, design_name)
        start_time = time.time()

        archive_run(design_build_dir, dirs=("power",))
        power_dir = design_build_dir / "power"
        gen_power_tcl(design, kernel_ctx.kernel, design_build_dir, power_dir,
                      kernel_ctx.threads_per_process)

        logging.info(f"Running PrimePower for {design_name}")

        # pt_shell reports PT-063 at startup, because this install has no Library
        # Compiler beside it. It reads the compiled library regardless.
        pt_shell = Path(RunConfig.load().tools["prime"]).expanduser() / "bin" / "pt_shell"

        log_path = design_build_dir / "logs" / "power.tessera.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w") as log:
            result = subprocess.run(
                [str(pt_shell), "-f", str((design_build_dir / "power.tcl").resolve())],
                cwd=power_dir,
                stdout=log,
                stderr=subprocess.STDOUT,
            )

        ok = log_elapsed(self.name, design_name, result.returncode, start_time)
        if ok:
            power = read_power(power_dir)
            update_manifest(design_build_dir, power=power)
            logging.info(f"  {design_name} uses {power['total'] * 1e6:.1f} uW")
        return ok
