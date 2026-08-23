from tessera.flows.base import Flow


class GLS(Flow):
    "Simulate the gate netlist against the testbench the RTL passed"
    name = "Gate level simulation"
    stage = "gls"

    def run(self, design, kernel_ctx):
        # patch the scverify makefile to hold the netlist, then run it
        pass
