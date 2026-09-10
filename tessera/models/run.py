"""
Run-wide state, fixed for the whole invocation.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Run:
    target: str # the kernel the run was asked to build
    is_fpga_run: bool
    threads: int
    threads_per_process: int
    workers: int
    sweep_flags: dict
    frm: str               # the stage range to run
    to: str
    root_dir: Path
