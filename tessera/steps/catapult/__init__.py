import logging
import time
import subprocess
from pathlib import Path

from tessera.const import DWARE_DIR
from tessera.models.config import RunConfig
from tessera.steps.base import Step
from tessera.steps.questagls.libs import build_dware
from tessera.helpers.archive import archive_run
from tessera.helpers.others import log_elapsed
from tessera.steps.catapult.comb import COMB_CHK_EXIT, mark_combinational
from tessera.steps.catapult.package import write_package
from tessera.steps.gen.codegen import gen_catapult_design_tcl, gen_kernel_top


class CatapultHLS(Step):
    """
    High level synthesis with Catapult HLS Ultra, C++ to RTL

    A design that schedules in one cycle can be built as a combinational CCORE: 
    Doing so reduces the latency. combinational CCOREs don't have a top level wrapper.
    Therefore, throughout the framework combinational designs are accounted for differently.
    """
    name = "hls"
    stages = ("cpp", "hls", "rtl")
    license = "catapult_ultra"
    multi_threaded = False

    def setup(self, kernel, designs, run_inst):
        # A blackboxed child's RTL names DesignWare parts Catapult did not map
        # itself, so its RTL verify needs their models compiled once
        if kernel.config.blackbox:
            logging.info(f"Compiling the DesignWare sim models")
            conf = RunConfig.load()
            log_path = DWARE_DIR / "dware.log"
            DWARE_DIR.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as log:
                build_dware(conf.tools["dc"], conf.tools["catapult"], conf.tools["questa"], log)

    @staticmethod
    def flags(run_inst, kernel):
        "What the kernel tcl reads, which the range decides rather than the sweep"
        from tessera.steps import has_stage
        return {
            **run_inst.sweep_flags,
            # The test runs inside catapult and is cheap, so a range that
            # synthesizes always includes it
            "test_cpp": has_stage("cpp", "gen", run_inst.to),
            # Stopping at cpp leaves catapult nothing to do after the test
            "test_cpp_only": run_inst.to == "cpp",
            "verify_rtl": has_stage("rtl", run_inst.frm, run_inst.to),
            # FPGA "syn" is Vivado inside Catapult. Run it only for the target.
            "run_vivado": has_stage("syn", run_inst.frm, run_inst.to)
                          and kernel.name == run_inst.target,
        }

    @staticmethod
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

    def run(self, design, kernel, run_inst):
        design_name = design.build_dir.name
        start_time = time.time()
        logging.info(f"Running Catapult for {design_name}")
        if self.flags(run_inst, kernel)["run_vivado"]:
            logging.info(f"Running Vivado FPGA for {design_name} after")

        # First Catapult run
        return_code = self.run_catapult(kernel.build_dir, design.build_dir)

        # After the first run, check if the design can be built as a combinational
        # By checking if the latency <= 1 cycle.
        latency_fp = design.build_dir / "Catapult" / "latency.txt"
        combinational = (return_code == COMB_CHK_EXIT and latency_fp.exists()
                         and int(latency_fp.read_text()) <= 1)
        mark_combinational(design.build_dir, combinational)

        # Second Catapult run if the design can be built as a combinational
        if combinational:
            logging.info(f"{design_name} schedules in one cycle, rebuilding as combinational")
            archive_run(design.build_dir, label="comb_chk_", dirs=("Catapult",))
            gen_kernel_top(design, kernel, combinational=True)
            gen_catapult_design_tcl(design, kernel, combinational=True)
            return_code = self.run_catapult(kernel.build_dir, design.build_dir)

        # A parent blackboxes the design through its package, so only a
        # successful run leaves one
        if return_code == 0:
            write_package(design, kernel, combinational)

        return log_elapsed(self.name, design_name, return_code, start_time)
