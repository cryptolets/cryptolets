from pathlib import Path
from itertools import product
import yaml
import json
import importlib

BUILD_DIR = Path('build')

def find_kernel(target_kernel):
    for level in Path('kernels').iterdir():
        for kernel in level.iterdir():
            if kernel.name == target_kernel:
                return kernel
    raise Exception(f"Kernel '{target_kernel}' not found")


def flatten_sweep(sweep):
    # TODO: We need to way to filter/override the sweep
    keys = list(sweep.keys())
    values = list(sweep.values())
    return [dict(zip(keys, combo)) for combo in product(*values)]


def call_gen_samples(design, kernel_path, design_build_dir):
    "Calls the gen_samples module for the given kernel"
    parts = kernel_path.parts
    idx = parts.index("kernels")
    module_name = ".".join(parts[idx:]) + ".gen_samples"
    
    mod = importlib.import_module(module_name)
    mod.generate(design, design_build_dir)


def get_design_dir_name(design):
    for k, v in design.items():
        if isinstance(v, bool):
            design[k] = int(v)

    return "__".join([f"{k}_{v}" for k, v in design.items()])


def run(kernel, threads, threads_per_process, sweep, run_only, dry_run, rtl, gui):
    kernel_build_dir = Path(BUILD_DIR, kernel)
    flattened_path = kernel_build_dir / 'flattened_sweep_config.json'

    # For run only assume flattened_sweep_config.json is already generated
    # so --sweep is not needed when --run-only is used
    assert not run_only or flattened_path.exists(), f"--run-only requires {flattened_path}"
    assert run_only or sweep, "--sweep is required when --run-only is not used"

    kernel_path = find_kernel(kernel)
    kernel_conf = yaml.safe_load(Path(kernel_path / 'kernel.yaml').read_text())

    # Create build directory to store ephemeral build files
    Path(BUILD_DIR, kernel).mkdir(parents=True, exist_ok=True)
    
    if not run_only:
        sweep_conf = yaml.safe_load(Path(sweep).read_text())
        flattened_sweep = flatten_sweep(sweep_conf['sweep'])
        sweep_flags = sweep_conf['flags']

        # Store flattened sweep configurations in JSON format
        flattened_path.write_text(
            json.dumps(
                {'flags': sweep_flags, 'sweep': flattened_sweep},
                indent=2
        ))
    else:
        sweep_conf = json.loads(Path(flattened_path).read_text())
        flattened_sweep = sweep_conf['sweep']
        sweep_flags = sweep_conf['flags']

    # For dry run we only generate the sweep configuration and exit
    if dry_run:
        print("Dry run. Build aborted.")
        return

    # TODO: Dependency resolution

    # TODO: Parallelize
    for design in flattened_sweep:
        design_build_dir = Path(kernel_build_dir, get_design_dir_name(design))
        call_gen_samples(design, kernel_path, design_build_dir)

    # TODO: Construct Catapult Yaml

    # TODO: Run Catapult

    # TODO: Select Designs (All, Pareto, Smallest, Fastest)

    # TODO: Externel flows (DC, Vivado)