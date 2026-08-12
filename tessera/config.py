"Validated configuration models"
import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, model_validator

CURVES_FILE = Path(__file__).parent.parent / "reference" / "curves.yaml"
ARB_CURVE = "arb_curve"  # follows n instead of fixing it


def _load(model, path):
    return model.model_validate(yaml.safe_load(Path(path).read_text()))


def curves():
    return yaml.safe_load(CURVES_FILE.read_text())


class Flags(BaseModel):
    syn: bool = False
    test_cpp: bool = True
    verify_rtl: bool = False
    test_cpp_only: bool = False
    num_test_samples: int = 10

    @model_validator(mode="after")
    def _rtl_verify_needs_cpp(self):
        # RTL verification reuses the samples and goldens that the C++ test generates
        if self.verify_rtl:
            self.test_cpp = True
        return self


class Sweep(BaseModel):
    bitwidth: list[int]
    tech_type: list[str] = ["gf12"]
    period: list[float] = [1]
    ii: list[int] = [1]

    # A named curve fixes n to its own bitwidth; arb_curve follows n
    curve: list[str] = [ARB_CURVE]
    field: list[str] = ["base"]
    q_type: list[str] = ["var_q"] # fixed_q bakes the modulus into the hardware, var_q takes it as a port
    
    # Keyed by n, e.g. {16: [8, 16], 32: [16, 32]}
    base_mul_width: Optional[dict[int, list[int]]] = None
    kar_base_mul_width: Optional[dict[int, list[int]]] = None

    @model_validator(mode="after")
    def _check_curves(self):
        known = curves()

        for name in self.field:
            if name not in ("base", "scalar"):
                raise ValueError(f"field must be 'base' or 'scalar', got '{name}'")

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


class RunConfig(BaseModel):
    total_threads: int = 8
    threads_per_process: int = 1
    run_only: bool = False
    dry_run: bool = False
    rtl_file: str = "rtl"
    gui_mode: bool = False

    @classmethod
    def load(cls, path):
        return _load(cls, path)
