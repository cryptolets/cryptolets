import csv
import random
from pathlib import Path

SAMPLES_PATH = Path("samples.csv")
GOLDENS_PATH = Path("goldens.csv")

def get_rng(seed=42):
    return random.Random(seed)

def _write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def write_csvs(samples, goldens, design_build_dir):
    samples_header = [f"i{i}" for i in range(len(samples[0]))]
    goldens_header = [f"o{i}" for i in range(len(goldens[0]))]
    _write_csv(design_build_dir / SAMPLES_PATH, samples_header, samples)
    _write_csv(design_build_dir / GOLDENS_PATH, goldens_header, goldens)