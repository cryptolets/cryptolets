"The stages a design goes through, in the order they run"
from tessera.flows.base import KernelContext, Flow, STAGES, has_stage
from tessera.flows.generate import Generate
from tessera.flows.catapult import Catapult
from tessera.flows.package import Package
from tessera.flows.syn import DesignCompiler
from tessera.flows.gls import GLS
from tessera.flows.power import PrimePower

# cpp and rtl are stages of the Catapult run, so the tcl carries them
FLOWS = [Generate(), Catapult(), Package(), DesignCompiler(), GLS(), PrimePower()]
