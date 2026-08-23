import subprocess
from pathlib import Path

# kernel.tcl exits with this when the design schedules in one cycle
COMB_CHK_EXIT = 2


def run_catapult(kernel_build_dir, design_build_dir):
    log_path = design_build_dir / "logs" / "catapult.tessera.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as log:
        result = subprocess.run(
            ["catapult", "-shell", "-file", str(Path(kernel_build_dir, 'kernel.tcl').resolve())],
            cwd=design_build_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        return result.returncode


# The rebuild archives the Catapult dir that held the latency, so the answer
# is kept beside the reports, where the package flow still finds it
COMB_MARK = Path("reports") / "combinational"


def is_combinational(design_build_dir):
    "Whether the design scheduled in one cycle, so it holds no state"
    return (design_build_dir / COMB_MARK).exists()


def mark_combinational(design_build_dir, combinational):
    "Record what the schedule came back as, for the flows that follow"
    mark = design_build_dir / COMB_MARK
    mark.parent.mkdir(parents=True, exist_ok=True)
    if combinational:
        mark.touch()
    elif mark.exists():
        mark.unlink()
