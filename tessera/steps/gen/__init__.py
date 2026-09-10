from pathlib import Path
import yaml

from tessera.steps.base import Step
from tessera.samples import write_test_samples
from tessera.steps.gen.blackbox import gen_blackbox_headers
from tessera.steps.catapult import CatapultHLS
from tessera.helpers.archive import archive_design
from tessera.steps.gen.codegen import (gen_catapult_design_tcl,
                                       gen_catapult_kernel_tcl,
                                       gen_kernel_top, gen_params_h)


class Generate(Step):
    "Generate all the files a design needs before other steps run"
    name = "gen"

    def setup(self, kernel, designs, run_inst):
        """
        Setup ran once per kernel to write kernel.tcl
        """
        kernel.build_dir.mkdir(parents=True, exist_ok=True)
        gen_catapult_kernel_tcl(CatapultHLS.flags(run_inst, kernel), kernel, run_inst)

    def run(self, design, kernel, run_inst):
        # A design that reaches here is not built, so its old files move aside
        archive_design(design.build_dir)

        # The dir is named by hash, so the design says what it is
        (design.build_dir / "design.yaml").write_text(yaml.safe_dump({
            "kernel": kernel.name,
            "hash": design.build_dir.name,
            "name": design.get_name(kernel.config.design_key),
            "params": design.design,
        }, sort_keys=False))
        write_test_samples(design, kernel, run_inst) # Write the test samples by calling gen_samples for the kernel
        gen_params_h(design)
        gen_kernel_top(design, kernel)
        if design.uses_blackboxes:
            gen_blackbox_headers(design, run_inst)
        gen_catapult_design_tcl(design, kernel, comb_chk=True)
        return True # success
