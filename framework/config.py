"Validated configuration models"
from pathlib import Path

import yaml
from pydantic import BaseModel, model_validator


def _load(model, path):
    return model.model_validate(yaml.safe_load(Path(path).read_text()))


class Flags(BaseModel):
    syn: bool = False
    test_cpp: bool = True
    verify_rtl: bool = False
    test_cpp_only: bool = False
    num_test_samples: int = 10
    ccore_top: bool = True

    @model_validator(mode="after")
    def _rtl_verify_needs_cpp(self):
        # RTL verification reuses the samples and goldens that the C++ test generates
        if self.verify_rtl:
            self.test_cpp = True
        return self


class Sweep(BaseModel):
    n: list[int]
    multi_word: list[bool] = [False]
    tech_type: list[str] = ["gf12"]
    period: list[float] = [1]
    ii: list[int] = [1]

    # Keyed by n, e.g. {16: [8, 16], 32: [16, 32]}
    base_mul_width: dict[int, list[int]] | None = None
    kar_base_mul_width: dict[int, list[int]] | None = None


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
