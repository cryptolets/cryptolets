import os
import logging
from pathlib import Path

from tessera.steps.base import Step
from tessera.models.config import RunConfig
from tessera.simlib import build_dware
from tessera.samples import write_test_samples
from tessera.steps.gen.blackbox import gen_blackbox_headers
from tessera.steps.catapult import CatapultHLS
from tessera.helper import archive_design
from tessera.const import DONE_DIR
from tessera.steps.gen.codegen import (gen_catapult_design_tcl,
                                            gen_catapult_kernel_tcl,
                                            gen_kernel_top, gen_params_h)
                                            

class Generate(Step):
    "Generate all the files a design needs before other steps run"
    name = "gen"

    def setup(self, kernel, run_inst):
        """
        Setup ran once per kernel to write kernel.tcl
        """
        kernel.build_dir.mkdir(parents=True, exist_ok=True)
        gen_catapult_kernel_tcl(CatapultHLS.flags(run_inst), kernel, run_inst)

        # Every design of a kernel shares the same arithmetic models, and only
        # a kernel that blackboxes something has to ask for them
        if kernel.config.blackbox:
            conf = RunConfig.load()

            # Build the one-time dware lib
            log_path = kernel.build_dir / "dware.log"
            logging.info(f"Compiling the DesignWare sim libs for {kernel.name}, "
                         f"once per kernel (see {log_path})")
            with log_path.open("w") as log:
                build_dware(conf.tools["dc"], kernel.build_dir,
                            conf.tools["catapult"], conf.tools["questa"],
                            os.environ, log)

    def run(self, design, kernel, run_inst):
        # If design is reused, don't archive the design, otherwise archive it
        reused = (kernel.name != run_inst.target
                  and (design.build_dir / DONE_DIR / "hls.done").exists())
        archive_design(design.build_dir, reused=reused)
        write_test_samples(design, kernel, run_inst) # Write the test samples by calling gen_samples for the kernel
        gen_params_h(design)
        gen_kernel_top(design, kernel)
        if design.uses_blackboxes:
            gen_blackbox_headers(design, run_inst.to == "gen")
        gen_catapult_design_tcl(design, kernel, comb_chk=True)
        return True # success
