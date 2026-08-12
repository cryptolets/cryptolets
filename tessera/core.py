from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import yaml
import json
import subprocess
import uuid
import logging
import time

from tessera.config import SweepConfig
from tessera.helper import get_design_dir_name
from tessera.kernel import find_kernel
from tessera.sweep import flatten_sweep
from tessera.helper import get_license_info
from tessera.samples import call_gen_samples
from tessera.codegen import \
    gen_catapult_design_tcl, gen_catapult_kernel_tcl, \
    gen_params_h, gen_kernel_src_cpp

BUILD_DIR = Path('build')


def run_catapult(kernel_build_dir, design_build_dir):
    log_path = design_build_dir / "catapult.tessera.log"
    with log_path.open("w") as log:
        result = subprocess.run(
            ["catapult", "-shell", "-file", str(Path(kernel_build_dir, 'kernel.tcl').resolve())],
            cwd=design_build_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        return result.returncode

def package_catapult_rtl(kernel, design_name, design_build_dir):
    "Copy the generated RTL into the design's package dir."
    solution_dir = design_build_dir / "Catapult" / f"{kernel}.v1"
    text = (solution_dir / "concat_rtl.v").read_text()

    # The top is the shortest match, since its _core child extends the same name.
    top = min((l.split()[1].rstrip("(") for l in text.splitlines()
               if l.startswith(f"module {kernel}")), key=len)

    dst = design_build_dir / "package" / f"{top}.v"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    return dst

def run_design_compiler(design_build_dir):
    pass


def run(kernel, threads, threads_per_process, sweep, run_only, dry_run, gui_mode):
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
        conf = SweepConfig.load(sweep)
        sweep_conf = conf.model_dump()
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
    enums = yaml.safe_load(Path(root_dir, 'tessera', 'enums.yaml').read_text())

    logging.info(f"Generating kernel files")
    logging.info(f"Flattened sweep designs:")
    for i, design in enumerate(flattened_sweep, 1):
        logging.info(f"  [{i}/{len(flattened_sweep)}] {get_design_dir_name(design)}")

    def _gen_kernel_files(design):
        design_name = get_design_dir_name(design)
        design_build_dir = Path(kernel_build_dir, design_name)

        # If a prior Catapult project exists, move it to a prior_catapult directory
        # and give it a unique name
        if design_build_dir.exists():
            prior_catapult_proj_dir = design_build_dir / "Catapult"
            prior_catapult_proj_ccs = design_build_dir / "Catapult.ccs"
            if prior_catapult_proj_dir.exists():
                prior_dir = design_build_dir / "prior_catapult" / f"Catapult_{uuid.uuid4().hex[:8]}"
                prior_dir.mkdir(parents=True, exist_ok=True)
                prior_catapult_proj_dir.rename(prior_dir / f"Catapult")
                if prior_catapult_proj_ccs.exists():
                    prior_catapult_proj_ccs.rename(prior_dir / f"Catapult.ccs")
        else:
            design_build_dir.mkdir(parents=True, exist_ok=True)

        if sweep_flags['test_cpp']:
            call_gen_samples(design, sweep_flags, kernel_path, design_build_dir)

        gen_params_h(design, enums, design_build_dir)
        gen_kernel_src_cpp(design, kernel, kernel_path, design_build_dir)
        gen_catapult_design_tcl(design, design_name, design_build_dir)
    
    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(_gen_kernel_files, flattened_sweep))

    gen_catapult_kernel_tcl(sweep_conf, kernel, kernel_path, kernel_build_dir, root_dir)

    # For dry run we only stop before running Catapult
    if dry_run:
        logging.warning("Dry run. Catapult run aborted.")
        return

    # Check license availability for each tool
    num_catapult_lics_available = get_license_info()['available']
    num_dc_lics_available = get_license_info("dc")['available']
    num_prime_power_lics_available = get_license_info("prime_power")['available']

    logging.info(f"{num_catapult_lics_available} Catapult Ultra licenses available")
    logging.info(f"{num_dc_lics_available} Design Compiler licenses available")
    logging.info(f"{num_prime_power_lics_available} PrimePower licenses available")

    num_catapult_workers = min(threads // threads_per_process, num_catapult_lics_available)
    if num_catapult_lics_available < num_catapult_workers:
        logging.warning(f"Not enough Catapult licenses available, using {num_catapult_workers} workers")

    # Run Catapult per designs in parallel
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
            package_catapult_rtl(kernel, design_name, design_build_dir)
            logging.info(f"Catapult RTL packaged for {design_name}")
        else:
            logging.error(f"Catapult FAILED for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")
    
    logging.info(f"Running Catapult")
    with ThreadPoolExecutor(max_workers=num_catapult_workers) as pool:
        list(pool.map(_run_catapult_worker, flattened_sweep))

    return
        
    # TODO: Select Designs (all, pareto, smallest, fastest)
    def _run_dc_worker(design):
        design_name = get_design_dir_name(design)
        logging.info(f"Running Design Compiler Synthesis for {design_name}")
        design_build_dir = Path(kernel_build_dir, design_name)
        start_time = time.time()
        return_code = run_catapult(kernel_build_dir, design_build_dir)
        time_elapsed = time.time() - start_time
        hrs, mins, secs = int(time_elapsed // 3600), int((time_elapsed % 3600) // 60), time_elapsed % 60

        if return_code == 0:
            logging.info(f"Catapult COMPLETED for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")
        else:
            logging.error(f"Catapult FAILED for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")
    # TODO: Externel flows (asic = dc -> vsc -> primepower, fpga = vivado)