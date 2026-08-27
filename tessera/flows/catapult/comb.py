import subprocess
from pathlib import Path

from tessera.const import COMB_MARK

COMB_CHK_EXIT = 2


def is_combinational(design_build_dir):
    "Check if the design is combinational"
    return (design_build_dir / COMB_MARK).exists()


def mark_combinational(design_build_dir, combinational):
    "Mark the design is combinational, if determined"
    mark = design_build_dir / COMB_MARK
    mark.parent.mkdir(parents=True, exist_ok=True)
    if combinational:
        mark.touch()
    elif mark.exists():
        mark.unlink()
