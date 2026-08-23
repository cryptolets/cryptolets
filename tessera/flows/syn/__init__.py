from tessera.flows.base import Flow


class DesignCompiler(Flow):
    "Logic synthesis, RTL to a gate netlist"
    name = "Design Compiler"
    stage = "syn"
    license = "dc"

    def designs(self, designs, kernel_ctx):
        # syn_sel takes all of them, the frontier, or the smallest and fastest
        pass

    def run(self, design, kernel_ctx):
        # run dc_shell, then record the area, delay and power it measured
        pass
