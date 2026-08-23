import logging
import time
import subprocess
from pathlib import Path

from tessera.flows.base import Flow
from tessera.helper import archive_run, get_design_dir_name, log_elapsed
from tessera.flows.catapult.comb import COMB_CHK_EXIT, mark_combinational
from tessera.flows.generate.codegen import \
        gen_catapult_design_tcl, gen_kernel_top


def run_catapult(kernel_build_dir, design_build_dir):
    log_path = design_build_dir / "logs" / "catapult.tessera.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as log:
        result = subprocess.run(
            ["catapult", "-shell", "-file", str(Path(kernel_build_dir, 'kernel.tcl').resolve())],
            cwd=design_build_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        return result.returncode


class Catapult(Flow):
    """
    High level synthesis with Catapult HLS Ultra, C++ to RTL
    """
    name = "Catapult"
    stage = "hls"
    license = "catapult_ultra"
    multi_threaded = False

    def run(self, design, kernel_ctx):
        design_name = get_design_dir_name(design, kernel_ctx.kernel)
        design_build_dir = Path(kernel_ctx.kernel_build_dir, design_name)
        start_time = time.time()

        logging.info(f"Running Catapult for {design_name}")
        return_code = run_catapult(kernel_ctx.kernel_build_dir, design_build_dir)

        # After the first run, check if the design can be built as a combinational
        # By checking if the latency <= 1 cycle.
        latency_fp = design_build_dir / "Catapult" / "latency.txt"
        combinational = (return_code == COMB_CHK_EXIT and latency_fp.exists()
                         and int(latency_fp.read_text()) <= 1)
        mark_combinational(design_build_dir, combinational)

        # A design that schedules in one cycle is rebuilt as a combinational
        # CCORE, which gives a lower latency design than a sequential one
        if combinational:
            logging.info(f"{design_name} schedules in one cycle, "
                         f"rebuilding as combinational")
            archive_run(design_build_dir, label="comb_chk_", dirs=("Catapult",))

            gen_kernel_top(design, kernel_ctx.kernel, kernel_ctx.impl_spec, design_build_dir,
                           combinational=True)
            gen_catapult_design_tcl(design, kernel_ctx.kernel, design_name,
                                    design_build_dir, combinational=True)
            return_code = run_catapult(kernel_ctx.kernel_build_dir, design_build_dir)

        return log_elapsed(self.name, design_name, return_code, start_time)
