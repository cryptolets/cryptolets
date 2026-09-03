"""
Run-wide state, fixed for the whole invocation.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Run:
    threads: int
    threads_per_process: int
    workers: int
    sweep_flags: dict
    frm: str               # the stage range to run
    to: str
    root_dir: Path
