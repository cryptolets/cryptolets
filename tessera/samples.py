"Generate samples for a kernel"
import csv
import random
import importlib
from pathlib import Path

from tessera.const import GOLDENS_PATH, SAMPLES_PATH
from tessera.structs.field import SEED

def get_rng(seed=SEED):
    return random.Random(seed)


def _write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def write_csvs(samples, goldens, design_build_dir):
    samples_header = [f"i{i}" for i in range(len(samples[0]))]
    goldens_header = [f"o{i}" for i in range(len(goldens[0]))]
    _write_csv(design_build_dir / SAMPLES_PATH, samples_header, samples)
    _write_csv(design_build_dir / GOLDENS_PATH, goldens_header, goldens)


def write_test_samples(design, kernel, run_inst):
    "Calls the gen_samples module for the given kernel"
    parts = kernel.path.parts
    idx = parts.index("kernels")
    module_name = ".".join(parts[idx:]) + ".gen_samples"

    mod = importlib.import_module(module_name)
    mod.generate(design, run_inst.sweep_flags)


def get_q(design):
    field = design.design["field"]
    return int(design.structs[field]["q"]["val"], 16)


def get_rc(design):
    field = design.design["field"]
    const = "q_prime" if design.design["mred"] == "mred_mont" else "mu"
    return int(design.structs[field][const]["val"], 16)


def get_cmul_const(design):
    struct = design.get_param_struct("cmul_const")
    return struct["w"], int(struct["val"], 16)