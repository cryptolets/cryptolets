from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import yaml
import json
import subprocess
import os
import uuid
import logging
import time

from cryptolets.codegen import gen_catapult_design_tcl, gen_catapult_kernel_tcl, gen_params_h
from cryptolets.helper import flatten_sweep, get_design_dir_name
from cryptolets.helper import get_catapult_license_info
from cryptolets.samples import call_gen_samples

BUILD_DIR = Path('build')

def find_kernel(target_kernel):
    for level in Path('kernels').iterdir():
        for kernel in level.iterdir():
            if kernel.name == target_kernel:
                return kernel
    raise Exception(f"Kernel '{target_kernel}' not found")
    

def run_catapult(kernel_build_dir, design_build_dir):
    log_path = design_build_dir / "catapult.framework.log"
    with log_path.open("w") as log:
        result = subprocess.run(
            ["catapult", "-shell", "-file", str(Path(kernel_build_dir, 'kernel.tcl').resolve())],
            cwd=design_build_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

        return result.returncode
    return -1


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

    logging.info(f"Running {len(flattened_sweep)} designs for {kernel}")

    # TODO: Dependency resolution

    logging.info(f"Generating kernel files")
    def _gen_kernel_files(design):
        design_name = get_design_dir_name(design)
        design_build_dir = Path(kernel_build_dir, design_name)

        # If a prior Catapult project exists, move it to a prior_catapult directory
        # and give it a unique name
        if design_build_dir.exists():
            prior_catapult_proj_dir = design_build_dir / "Catapult"
            if prior_catapult_proj_dir.exists():
                prior_dir = design_build_dir / "prior_catapult"
                prior_dir.mkdir(parents=True, exist_ok=True)
                prior_catapult_proj_dir.rename(prior_dir / f"Catapult_{uuid.uuid4().hex[:8]}")
        else:
            design_build_dir.mkdir(parents=True, exist_ok=True)

        if sweep_flags['test_cpp']:
            call_gen_samples(design, sweep_flags, kernel_path, design_build_dir)

        gen_params_h(design, design_build_dir)
        gen_catapult_design_tcl(design, design_name, design_build_dir)
    
    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(_gen_kernel_files, flattened_sweep))

    gen_catapult_kernel_tcl(sweep_conf, kernel, kernel_path, kernel_build_dir, root_dir)

    # For dry run we only stop before running Catapult
    if dry_run:
        logging.warning("Dry run. Catapult run aborted.")
        return

    # Run Catapult per design parallelly
    num_catapult_lics_available = get_catapult_license_info()['available']
    logging.info(f"{num_catapult_lics_available} Catapult Ultra licenses available")
    num_catapult_workers = min(threads // threads_per_process, num_catapult_lics_available)
    if num_catapult_lics_available < num_catapult_workers:
        logging.warning(f"Not enough Catapult licenses available, using {num_catapult_workers} workers")

    def _run_catapult_worker(design):
        design_name = get_design_dir_name(design)
        logging.info(f"Running Catapult for {design_name}")
        design_build_dir = Path(kernel_build_dir, design_name)
        start_time = time.time()
        return_code = run_catapult(kernel_build_dir, design_build_dir)
        time_elapsed = time.time() - start_time
        hrs, mins, secs = int(time_elapsed // 3600), int((time_elapsed % 3600) // 60), time_elapsed % 60

        if return_code == 0:
            logging.info(f"Catapult COMPLETED for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")
        else:
            logging.error(f"Catapult FAILED for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")
    
    logging.info(f"Running Catapult")
    with ThreadPoolExecutor(max_workers=num_catapult_workers) as pool:
        list(pool.map(_run_catapult_worker, flattened_sweep))
        
    # TODO: Select Designs (All, Pareto, Smallest, Fastest)
    # TODO: Externel flows (DC, Vivado)