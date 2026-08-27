# What --from, --to and --only name, in the order they run
STAGES = ["gen", "cpp", "hls", "rtl", "syn", "gls", "pwr"]


def has_stage(stage, frm, to):
    "Whether a stage falls inside the range asked for"
    return STAGES.index(frm) <= STAGES.index(stage) <= STAGES.index(to)


class Flow:
    """
    One stage of the build, run over a kernel's designs
    """
    name = ""

    # The stage --from, --to and --only name. Several flows share one when
    # they always run together, so only the stage is selectable.
    stage = ""

    # The license the tool checks out, so the pool is capped by what is free
    license = None

    # Catapult holds one thread per process, the rest take what they are given
    multi_threaded = True

    def designs(self, designs, kernel_ctx):
        "The designs to run on, narrowed by what an earlier flow measured"
        return designs

    def run(self, design, kernel_ctx):
        "Run the stage for one design, and return whether it passed"
        raise NotImplementedError
