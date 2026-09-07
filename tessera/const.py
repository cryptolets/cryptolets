"""
All constants for Tessera
"""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
KERNELS_DIR = Path("kernels")
TEMPLATES_DIR = Path(__file__).parent / "templates"
CURVES_FILE = ROOT_DIR / "reference" / "curves.yaml"
RUN_CONFIG_FILE = Path("config.yaml")

BUILD_DIR = Path("build") # where Tessera writes its builds
RUNS_DIR = BUILD_DIR / "runs" # Each run's log, kept beside the builds it made
DWARE_DIR = (BUILD_DIR / "dware").resolve() # DesignWare sim models, built once
CELLS_DIR = (BUILD_DIR / "cells").resolve() # cell sim models, built once per tech

# emphemeral file to store the flattened and filtered sweep config
FLATTENED_SWEEP_FILE = "flattened_sweep_config.json"

SAMPLES_PATH = Path("test/samples.csv") # path to the samples file
GOLDENS_PATH = Path("test/goldens.csv") # path to the goldens file

COMB_MARK = Path("reports") / "combinational"
DONE_DIR = "done"

ARB_FIELD = "arb_field" # arbitrary prime field, not tied to any curve

# parameters that are hardware constrains, and not design parameters
HW_CONSTRAINTS_PARAMS = ["tech_type", "period", "ii", "dep_period_ratio"]