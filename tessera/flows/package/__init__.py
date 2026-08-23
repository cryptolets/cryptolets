import logging
from pathlib import Path

from tessera.flows.base import Flow
from tessera.flows.catapult.tool import is_combinational
from tessera.helper import get_design_dir_name
from tessera.flows.package.write import write_package


class Package(Flow):
    "Collect what Catapult built into RTL a parent can blackbox"
    name = "Package"
    stage = "hls"

    def run(self, design, kernel_ctx):
        design_name = get_design_dir_name(design, kernel_ctx.kernel)
        design_build_dir = Path(kernel_ctx.kernel_build_dir, design_name)

        write_package(kernel_ctx.kernel, design, design_build_dir,
                      is_combinational(design_build_dir), kernel_ctx.impl_spec)
        logging.info(f"Catapult RTL packaged for {design_name}")
        return True
