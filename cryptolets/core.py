from pathlib import Path
import yaml
import json
import importlib
import subprocess
import os

from cryptolets.codegen import gen_catapult_yaml, gen_params_h
from cryptolets.helper import flatten_sweep, unflatten_sweep, get_design_dir_name

BUILD_DIR = Path('build')

def find_kernel(target_kernel):
    for level in Path('kernels').iterdir():
        for kernel in level.iterdir():
            if kernel.name == target_kernel:
                return kernel
    raise Exception(f"Kernel '{target_kernel}' not found")


def call_gen_samples(design, kernel_path, design_build_dir):
    "Calls the gen_samples module for the given kernel"
    parts = kernel_path.parts
    idx = parts.index("kernels")
    module_name = ".".join(parts[idx:]) + ".gen_samples"
    
    mod = importlib.import_module(module_name)
    mod.generate(design, design_build_dir)


def run_catapult(kernel_build_dir, root_dir, threads):
    env = {
        **os.environ,
        "THREADS": str(threads),
        "SWEEP_YAML": str(Path(kernel_build_dir, 'sweep.yaml').resolve()),
        "ROOT_DIR": str(root_dir),
    }

    subprocess.run(
        ["catapult", "-shell", "-file", str(Path(root_dir, 'cryptolets', 'tcl', 'main.tcl'))],
        env=env,
        check=True,
        cwd=kernel_build_dir,
    )


def run(kernel, threads, threads_per_process, sweep, run_only, dry_run, rtl, gui):
    kernel_build_dir = Path(BUILD_DIR, kernel)
    flattened_path = kernel_build_dir / 'flattened_sweep_config.json'
    root_dir = Path(__file__).parent.parent

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
        flattened_sweep = sweep_conf['flattened_sweep']
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
        gen_params_h(design, design_build_dir)

    # We unflatten again to ensure manual changes to
    # flattened_sweep_config.json are reflected during catapult sweep
    sweep_conf['sweep'] = unflatten_sweep(flattened_sweep)
    gen_catapult_yaml(sweep_conf, kernel, kernel_path, kernel_build_dir, root_dir)

    # Run Catapult with main.tcl script
    run_catapult(kernel_build_dir, root_dir, threads)

    # TODO: Select Designs (All, Pareto, Smallest, Fastest)

    # TODO: Externel flows (DC, Vivado)