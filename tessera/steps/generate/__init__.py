import os
from pathlib import Path

from tessera.steps.generate.blackbox import gen_blackbox_headers
from tessera.steps.base import Flow
from tessera.models.config import RunConfig
from tessera.models.kernel import KernelConfig
from tessera.helper import (archive_design, get_design_dir_name,
                            is_done)
from tessera.simlib import build_dware
from tessera.samples import call_gen_samples
from tessera.steps.base import has_stage
from tessera.steps.generate.codegen import (gen_catapult_design_tcl,
                                            gen_catapult_kernel_tcl,
                                            gen_kernel_top, gen_params_h)


def catapult_flags(kernel_ctx):
    "What the kernel tcl reads, which the range decides rather than the sweep"
    return {
        **kernel_ctx.sweep_flags,
        # The test runs inside catapult and is cheap, so a range that
        # synthesizes always includes it
        "test_cpp": has_stage("cpp", "gen", kernel_ctx.to),
        # Stopping at cpp leaves catapult nothing to do after the test
        "test_cpp_only": kernel_ctx.to == "cpp",
        "verify_rtl": has_stage("rtl", kernel_ctx.frm, kernel_ctx.to),
    }


class Generate(Flow):
    "Generate all the files a design needs before other flows run"
    name = "Generation"
    stage = "gen"

    def designs(self, designs, kernel_ctx):
        # One tcl drives every design of a kernel, so it is written once
        kernel_ctx.kernel_build_dir.mkdir(parents=True, exist_ok=True)
        gen_catapult_kernel_tcl(catapult_flags(kernel_ctx), kernel_ctx.kernel, kernel_ctx.kernel_path,
                                kernel_ctx.kernel_build_dir, kernel_ctx.root_dir,
                                kernel_ctx.threads_per_process)

        # Every design of a kernel shares the same arithmetic models, and only
        # a kernel that blackboxes something has to ask for them
        if KernelConfig.load(kernel_ctx.kernel_path).blackbox:
            conf = RunConfig.load()
            log_path = kernel_ctx.kernel_build_dir / "dware.log"
            with log_path.open("w") as log:
                build_dware(conf.tools["dc"], kernel_ctx.kernel_build_dir,
                            conf.tools["catapult"], conf.tools["questa"],
                            os.environ, log)
        return designs

    def run(self, design, kernel_ctx):
        design_name = get_design_dir_name(design, kernel_ctx.kernel)
        design_build_dir = Path(kernel_ctx.kernel_build_dir, design_name)

        # A finished run is kept, so the next one starts from clean sources. A
        # dependency that is only reused built nothing of its own to keep, and
        # its marks say which stages it still holds.
        reused = (kernel_ctx.kernel != kernel_ctx.parent
                  and is_done(kernel_ctx.kernel, design, "hls"))
        if design_build_dir.exists() and not reused:
            archive_design(design_build_dir)
        else:
            design_build_dir.mkdir(parents=True, exist_ok=True)

        if catapult_flags(kernel_ctx)["test_cpp"]:
            call_gen_samples(design, kernel_ctx.sweep_flags, kernel_ctx.kernel_path,
                             design_build_dir)

        gen_params_h(design, design_build_dir)
        gen_kernel_top(design, design_build_dir, kernel_ctx)
        blackboxed = gen_blackbox_headers(
            design, kernel_ctx.kernel_path, kernel_ctx.impl_spec,
            design_build_dir, kernel_ctx.to == "gen")
        gen_catapult_design_tcl(design, kernel_ctx.kernel, design_name,
                                design_build_dir, blackboxed, comb_chk=True)
        return True
