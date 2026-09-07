import logging
import subprocess
import time
from pathlib import Path

from tessera.models.config import RunConfig
from tessera.steps.base import Step
from tessera.steps.catapult.package import update_manifest
from tessera.steps.primepower.codegen import gen_power_tcl
from tessera.parser.metrics.primepower import parse_primepower
from tessera.helpers.archive import archive_run
from tessera.helpers.others import log_elapsed


class PrimePower(Step):
    "Measure power from the activity a gate level simulation recorded"
    name = "pwr"
    license = "prime_power"

    def run(self, design, kernel, run_inst):
        design_name = design.build_dir.name
        start_time = time.time()
        logging.info(f"Running PrimePower for {design_name}")

        archive_run(design.build_dir, dirs=("power",))
        gen_power_tcl(design, kernel, run_inst)

        pt_shell = Path(RunConfig.load().tools["prime"]).expanduser() / "bin" / "pt_shell"
        power_dir = design.build_dir / "power"
        log_path = design.build_dir / "logs" / "power.tessera.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with log_path.open("w") as log:
            result = subprocess.run(
                [str(pt_shell), "-f", str((design.build_dir / "power.tcl").resolve())],
                cwd=power_dir,
                stdout=log,
                stderr=subprocess.STDOUT,
            )

        ok = log_elapsed(self.name, design_name, result.returncode, start_time)
        if ok:
            update_manifest(design, power=parse_primepower(design))
        return ok
