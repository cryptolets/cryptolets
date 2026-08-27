"Generate samples for a kernel"
import csv
import random
import importlib
from pathlib import Path

from tessera.const import GOLDENS_PATH, SAMPLES_PATH
from tessera.field import SEED, get_modulus

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

def call_gen_samples(design, sweep_flags, kernel_path, design_build_dir):
    "Calls the gen_samples module for the given kernel"
    parts = kernel_path.parts
    idx = parts.index("kernels")
    module_name = ".".join(parts[idx:]) + ".gen_samples"
    
    mod = importlib.import_module(module_name)
    mod.generate(design, sweep_flags, design_build_dir)