"Move a finished run aside, so the next one starts clean"
import uuid


KEEP = ("prior", "ccore_cache") # these don't get archived

def _move(design_build_dir, names, label):
    if not names:
        return

    run_dir = design_build_dir / "prior" / f"run_{label}{uuid.uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (design_build_dir / name).rename(run_dir / name)


def archive_run(design_build_dir, label="", dirs=("Catapult", "dc")):
    "Move a finished run's tool directories aside, so the next one starts clean"
    if "Catapult" in dirs:
        dirs = (*dirs, "Catapult.ccs")

    _move(design_build_dir, [d for d in dirs if (design_build_dir / d).exists()],
          label)


def archive_design(design_build_dir, label=""):
    """
    Ready a design dir: the previous run is moved aside, so the next one
    starts clean.
    """
    if design_build_dir.exists():
        _move(design_build_dir,
              [p.name for p in design_build_dir.iterdir() if p.name not in KEEP],
              label)
    design_build_dir.mkdir(parents=True, exist_ok=True)
