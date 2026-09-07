"""
Pydantic models for sweep files.
"""
from typing import Literal, Optional, get_args

from pydantic import BaseModel, model_validator

from tessera.const import ARB_FIELD
from tessera.models.common import load_and_validate_yaml, load_curves, is_fpga
from tessera.models.config import RunConfig


class Sweep(BaseModel):
    bitwidth: list[int]
    tech_type: list[str]
    period: list[float]
    ii: list[int] # initation interval in HLS a.k.a throughput

    # Blackboxed deps are built at period * ratio, so a chain of them fits
    # the parent's clock. Applied again at each level of depth.
    # Helps meet timing constraints of the parent
    dep_period_ratio: Optional[list[float]] = [1]

    # A named curve fixes n to its own bitwidth; arb_field follows n
    field: Optional[list[str]] = None
    mred: Optional[list[Literal["mred_mont", "mred_bar"]]] = None # montgomery or barrett reduction

    # fixed hardwires the const into the hardware, for mults, this uses a sometimes cheaper constant multiplier
    q_type: Optional[list[Literal["fixed_q", "var_q"]]] = None # modulus prime q

    # reduction constant q_prime for montgomery reduction and mu for barrett reduction
    redc_type: Optional[list[Literal["fixed_rc", "var_rc"]]] = None

    # normal (DesignWare mults), schoolbook, karatsuba multipliers
    mul_type: Optional[list[Literal["mul_nor", "mul_sb", "mul_kar"]]] = None
    skip_upper: Optional[list[int]] = None

    # which constant to use, specifically for the l0_int_cmul kernel
    cmul_const: Optional[list[str]] = None
    cmul_const_w: Optional[list[int]] = None
    cmul_hamming: Optional[list[float]] = None

    # which part of the product a cmul keeps
    cmul_output_type: Optional[list[Literal[
        "cmul_output_full", "cmul_output_lo", "cmul_output_hi"
    ]]] = None

    # point addtion formula selections
    pdbl_form: Optional[list[Literal["pdbl_a0", "pdbl_a3", "pdbl_avar"]]] = None
    padd_te_form: Optional[list[Literal["padd_te_add", "padd_te_cyclone"]]] = None

    # Keyed by n, e.g. {16: [8, 16], 32: [16, 32]}
    # TODO: We can autogenerate this list given rough base width constraint
    base_mul_width: Optional[dict[int, list[int]]] = None
    kar_base_mul_width: Optional[dict[int, list[int]]] = None

    @classmethod
    def enums(cls):
        """
        Returns enums for each sweep key, which are then
        used to generate the params.h defines.
        """
        out = {}
        for name, field in cls.model_fields.items():
            for arg in get_args(field.annotation) or ():
                values = get_args(get_args(arg)[0]) if get_args(arg) else ()
                if values and all(isinstance(v, str) for v in values):
                    out[name] = list(values)
                    break
        return out

    @model_validator(mode="after")
    def _check_tech(self):
        known_tech = RunConfig.load().tech
        for name in self.tech_type:
            if name not in known_tech:
                raise ValueError(f"unknown tech_type '{name}', pick from: {', '.join(sorted(known_tech))}")

        # The two report different things and take different flows, so a sweep
        # holding both would compare designs that cannot be compared
        if len({is_fpga(name) for name in self.tech_type}) > 1:
            raise ValueError("a sweep is either FPGA or ASIC, not both")
        return self

    @model_validator(mode="after")
    def _check_fields(self):
        if self.field:
            valid = {ARB_FIELD} | set(load_curves())
            for name in self.field:
                if name not in valid:
                    raise ValueError(f"unknown field '{name}', pick from: {', '.join(sorted(valid))}")
        return self

class SweepFlags(BaseModel):
    # Selects which designs go through logic synthesis
    syn_sel: Literal["all", "pareto", "small_fast"]

    # number of test samples for each design for C++/HLS-RTL/GLS Simulation/Verification
    num_test_samples: int = 100

    # compile_ultra passes in synthesis: one full, the rest incremental
    syn_passes: int = 1


class SweepConfig(BaseModel):
    sweep: Sweep
    flags: SweepFlags

    @classmethod
    def load(cls, path):
        return load_and_validate_yaml(cls, path)


def get_sweep_enum_vars():
    return {value: value
            for values in Sweep.enums().values() for value in values}

