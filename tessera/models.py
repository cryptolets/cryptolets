"""
Pydantic models for yaml files
"""
import logging
from pathlib import Path
from typing import Literal, Optional, get_args

import yaml
from pydantic import BaseModel, model_validator

CURVES_FILE = Path(__file__).parent.parent / "reference" / "curves.yaml"
RUN_CONFIG_FILE = Path("config.yaml")
ARB_CURVE = "arb_curve"


def load_and_validate_yaml(model, path):
    return model.model_validate(yaml.safe_load(Path(path).read_text()))


def curves():
    return yaml.safe_load(CURVES_FILE.read_text())


def is_fpga(tech_type):
    "An FPGA tech node uses fgpa prefix as convention in Tessera"
    return tech_type.startswith("fpga")


class Sweep(BaseModel):
    bitwidth: list[int]
    tech_type: list[str]
    period: list[float]
    ii: list[int] # initation interval in HLS a.k.a throughput

    # Blackboxed deps are built at period * ratio, so a chain of them fits
    # the parent's clock. Applied again at each level of depth.
    # Helps meet timing constraints of the parent
    dep_period_ratio: list[float] = [1]

    # A named curve fixes n to its own bitwidth; arb_curve follows n
    curve: list[str]
    field: list[Literal["base", "scalar"]] # base vs scalar fields for an elliptic curve
    mred: list[Literal["mred_mont", "mred_bar"]] # montgomery or barrett reduction

    # fixed hardwires the const into the hardware, for mults, this uses a sometimes cheaper constant multiplier
    q_type: list[Literal["fixed_q", "var_q"]] # modulus prime q

    # reduction constant q_prime for montgomery reduction and mu for barrett reduction
    redc_type: list[Literal["fixed_rc", "var_rc"]]
    
    # normal (DesignWare mults), schoolbook, karatsuba multipliers
    mul_type: list[Literal["mul_nor", "mul_sb", "mul_kar"]]
    skip_upper: list[int]

    # which constant to use, specifically for the l0_int_cmul kernel
    cmul_const: list[Literal[
        "cmul_q", "cmul_q_prime", "cmul_mu", "cmul_a", "cmul_b", "cmul_d", "cmul_k"
    ]]

    # point addtion formula selections
    pdbl_form: list[Literal["pdbl_a0", "pdbl_a3", "pdbl_avar"]] = ["pdbl_a0"]
    padd_te_form: list[Literal["padd_te_add", "padd_te_cyclone"]] = ["padd_te_add"]

    # Keyed by n, e.g. {16: [8, 16], 32: [16, 32]}
    # TODO: We can autogenerate this list given rough base width constraint
    base_mul_width: Optional[dict[int, list[int]]] = None
    kar_base_mul_width: Optional[dict[int, list[int]]] = None

    @classmethod
    def enums(cls):
        "Fields limited to a set of values, which become the params.h defines"
        out = {}
        for name, field in cls.model_fields.items():
            item_type = get_args(field.annotation)   # list[X] -> (X,)
            values = get_args(item_type[0]) if item_type else ()
            if values and all(isinstance(v, str) for v in values):
                out[name] = list(values)
        return out

    @model_validator(mode="after")
    def _check_curves(self):
        known_tech = RunConfig.load().tech
        for name in self.tech_type:
            if name not in known_tech:
                raise ValueError(f"unknown tech_type '{name}', pick from: {', '.join(sorted(known_tech))}")

        # The two report different things and take different flows, so a sweep
        # holding both would compare designs that cannot be compared
        if len({is_fpga(name) for name in self.tech_type}) > 1:
            raise ValueError("a sweep is either FPGA or ASIC, not both")

        known = curves()

        for name in self.curve:
            if name == ARB_CURVE:
                continue
            if name not in known:
                raise ValueError(f"unknown curve '{name}', pick from: {ARB_CURVE}, {', '.join(sorted(known))}")
            for field in self.field:
                if field not in known[name]:
                    logging.warning(f"curve '{name}' has no {field} field, skipping that combination")

        return self


class SweepFlags(BaseModel):
    # Selects which designs go through logic synthesis
    syn_sel: Literal["all", "pareto", "small_fast"]

    # number of test samples for each design for C++/HLS-RTL/GLS Simulation/Verification
    num_test_samples: int = 100


class SweepConfig(BaseModel):
    sweep: Sweep
    flags: SweepFlags

    @classmethod
    def load(cls, path):
        return load_and_validate_yaml(cls, path)


class KernelConfig(BaseModel):
    blackbox: list[str] = [] # which dependent kernels get blackkboxed
    # parameters specific to the design, which helps use group
    # designs for given kernel which perform the same arithmetic operation 
    design_key: list[str] = []
    kernel_key: list[str] = [] # parameters specific to the kernel
    stages: dict[str, str] = {}

    @model_validator(mode="after")
    def _kernel_key_is_part_of_the_design(self):
        extra = set(self.kernel_key) - set(self.design_key or self.kernel_key)
        if extra:
            raise ValueError(
                f"{', '.join(sorted(extra))} decide what the kernel computes, "
                f"so they belong in design_key as well")
        return self

    @classmethod
    def load(cls, kernel_path):
        return load_and_validate_yaml(cls, Path(kernel_path, "kernel.yaml"))


class TechNode(BaseModel):
    """
    Model for the technology node in config.yaml
    """
    catapult_lib_name: str
    vendor: str
    technology: str
    
    # ASIC specific
    lib_path: Optional[str] = None
    lib_db: Optional[str] = None
    catapult_lib_file: Optional[str] = None
    lib_verilog: Optional[str] = None
    lib_verilog_defines: Optional[str] = None

    # FPGA specific
    family: Optional[str] = None
    speed: Optional[str] = None
    part: Optional[str] = None


class RunConfig(BaseModel):
    """
    Load from config.yaml
    """
    total_threads: int
    threads_per_process: int
    min_free_gb: int
    frm: str
    to: str
    tools: dict[str, str] = {}
    tech: dict[str, TechNode] = {}

    @classmethod
    def load(cls, path=RUN_CONFIG_FILE):
        return load_and_validate_yaml(cls, path)
