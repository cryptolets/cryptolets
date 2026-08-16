"Validated configuration models"
import logging
from pathlib import Path
from typing import Literal, Optional, get_args

import yaml
from pydantic import BaseModel, model_validator

CURVES_FILE = Path(__file__).parent.parent / "reference" / "curves.yaml"
RUN_CONFIG_FILE = Path("config.yaml")
ARB_CURVE = "arb_curve"

def _load(model, path):
    return model.model_validate(yaml.safe_load(Path(path).read_text()))

def curves():
    return yaml.safe_load(CURVES_FILE.read_text())


class Flags(BaseModel):
    syn: bool = False
    gls: bool = False
    test_cpp: bool = True
    verify_rtl: bool = False
    test_cpp_only: bool = False
    num_test_samples: int = 10

    @model_validator(mode="after")
    def _enable_what_each_stage_needs(self):
        # Gate level simulation runs the RTL testbench against the synthesized
        # netlist, so it needs both a netlist and that testbench
        if self.gls:
            self.syn = True
            self.verify_rtl = True

        # RTL verification reuses the samples and goldens that the C++ test generates
        if self.verify_rtl:
            self.test_cpp = True
        return self


class Sweep(BaseModel):
    bitwidth: list[int]
    tech_type: list[str] = ["gf12_highperf"]
    period: list[float] = [1]
    ii: list[int] = [1]

    # Blackboxed deps are built at period * ratio, so a chain of them fits
    # the parent's clock. Applied again at each level of depth.
    dep_period_ratio: list[float] = [1]

    # A named curve fixes n to its own bitwidth; arb_curve follows n
    curve: list[str] = [ARB_CURVE]
    field: list[Literal["base", "scalar"]] = ["base"]
    q_type: list[Literal["fixed_q", "var_q"]] = ["var_q"] # fixed_q bakes the modulus into the hardware, var_q takes it as a port

    # Keyed by n, e.g. {16: [8, 16], 32: [16, 32]}
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


class SweepConfig(BaseModel):
    sweep: Sweep
    flags: Flags = Flags()

    @classmethod
    def load(cls, path):
        return _load(cls, path)


class KernelConfig(BaseModel):
    deps: list[str] = []
    stages: dict[str, str] = {}

    @classmethod
    def load(cls, kernel_path):
        return _load(cls, Path(kernel_path, "kernel.yaml"))


class Tech(BaseModel):
    lib_path: str
    catapult_lib_name: str
    lib_db: str
    vendor: str
    technology: str
    catapult_lib_file: Optional[str] = None
    # Behavioural models of the cells, which gate level simulation needs to
    # know what a cell does. A tech without them cannot run one.
    lib_verilog: Optional[str] = None
    # Vendor macros the models are compiled with. ARM needs its unknown squash,
    # or the cells hold X and the first transaction compares as a wrong answer.
    lib_verilog_defines: str = ""


class RunConfig(BaseModel):
    total_threads: int = 8
    threads_per_process: int = 1
    run_only: bool = False
    dry_run: bool = False
    rtl_file: str = "rtl"
    gui_mode: bool = False

    tools: dict[str, str] = {}
    tech: dict[str, Tech] = {}

    @classmethod
    def load(cls, path=RUN_CONFIG_FILE):
        return _load(cls, path)
