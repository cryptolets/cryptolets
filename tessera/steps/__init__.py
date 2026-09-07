"The pipeline: the steps a design goes through, in the order they run"
from tessera.steps.base import Step
from tessera.steps.gen import Generate
from tessera.steps.catapult import CatapultHLS
from tessera.steps.dc import DesignCompiler
from tessera.steps.questagls import QuestaSimGLS
from tessera.steps.primepower import PrimePower

# Swap a step by editing this list, e.g. QuestaSimGLS() -> VCSGLS()
PIPELINE = [Generate(), CatapultHLS(), DesignCompiler(), QuestaSimGLS(), PrimePower()]

# The checkpoints --from and --to can name, derived from the steps
STAGES = [stage for step in PIPELINE for stage in step.stages]


def has_stage(stage, frm, to):
    "Whether a stage falls inside the range asked for"
    return STAGES.index(frm) <= STAGES.index(stage) <= STAGES.index(to)
