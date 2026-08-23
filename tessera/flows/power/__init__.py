from tessera.flows.base import Flow


class PrimePower(Flow):
    "Measure power from the activity a gate level simulation recorded"
    name = "PrimePower"
    stage = "pwr"
    license = "prime_power"

    def run(self, design, kernel_ctx):
        # annotate the vcd onto the netlist, then record the total
        pass
