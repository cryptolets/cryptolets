from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import yaml
import subprocess
import uuid
import logging
import time

from tessera.config import SweepConfig, RunConfig, KernelConfig
from tessera.helper import get_design_dir_name
from tessera.kernel import find_kernel
from tessera.sweep import flatten_sweep
from tessera.helper import get_license_info
from tessera.samples import call_gen_samples
from tessera.codegen import \
    gen_catapult_design_tcl, gen_catapult_kernel_tcl, \
    gen_params_h, gen_kernel_top, read_impl_spec
from tessera.package import write_package, update_manifest
from tessera.blackbox import gen_blackbox_headers
from tessera.syn import gen_dc_tcl, read_dc_area, read_dc_delay, read_dc_power
from tessera.gls import gen_gls_makefile, run_gls
from tessera.power import gen_power_tcl, read_power
from tessera.select import select_designs
from tessera.schedule import resolve, log_schedule, to_build, BUILD_DIR

# kernel.tcl exits with this when the design schedules in one cycle
COMB_CHK_EXIT = 2


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

def archive_run(design_build_dir, label="", dirs=("Catapult", "dc")):
    "Move a finished run's tool directories aside, so the next one starts clean"
    if "Catapult" in dirs:
        dirs = (*dirs, "Catapult.ccs")

    stale = [d for d in dirs if (design_build_dir / d).exists()]
    if not stale:
        return

    run_dir = design_build_dir / "prior" / f"run_{label}{uuid.uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in stale:
        (design_build_dir / name).rename(run_dir / name)


def run_flow(tool, worker, designs, workers, license=None, dry_run=False):
    """
    A general wrapper to run one tool over every design, as far as its licenses allow.
    """
    # A dry run only writes the files the tool would read, so it skips the license check.
    if license and not dry_run:
        available = get_license_info(license)['available']
        logging.info(f"{available} {tool} licenses available")
        if available < workers:
            logging.warning(f"Not enough {tool} licenses available, using {available} workers")
        workers = min(workers, available)

    logging.info(f"{'Generating files for' if dry_run else 'Running'} {tool}")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(worker, designs))


def log_elapsed(tool, design_name, return_code, start_time):
    elapsed = time.time() - start_time
    hrs, mins, secs = int(elapsed // 3600), int((elapsed % 3600) // 60), elapsed % 60
    status = "COMPLETED" if return_code == 0 else "FAILED"
    log = logging.info if return_code == 0 else logging.error
    log(f"{tool} {status} for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")


def gen_kernel_files(design, kernel, kernel_path, kernel_build_dir, impl_spec,
                     sweep_flags, dry_run=False):
    design_name = get_design_dir_name(design, kernel)
    design_build_dir = Path(kernel_build_dir, design_name)

    # A finished run is kept, so the next one starts from clean sources
    if design_build_dir.exists():
        archive_run(design_build_dir)
    else:
        design_build_dir.mkdir(parents=True, exist_ok=True)

    if sweep_flags['test_cpp']:
        call_gen_samples(design, sweep_flags, kernel_path, design_build_dir)

    gen_params_h(design, design_build_dir)
    gen_kernel_top(design, kernel, impl_spec, design_build_dir)
    gen_blackbox_headers(design, kernel_path, impl_spec, design_build_dir, dry_run)
    gen_catapult_design_tcl(design, kernel, design_name, design_build_dir, comb_chk=True)


def catapult_worker(design, kernel, kernel_build_dir, impl_spec):
    design_name = get_design_dir_name(design, kernel)
    logging.info(f"Running Catapult for {design_name}")
    design_build_dir = Path(kernel_build_dir, design_name)
    start_time = time.time()

    # A kernel that schedules in one cycle is rebuilt as combinational, which
    # gives a lower latency design than a sequential one would
    return_code = run_catapult(kernel_build_dir, design_build_dir)

    latency_fp = design_build_dir / "Catapult" / "latency.txt"
    combinational = (return_code == COMB_CHK_EXIT and latency_fp.exists()
                     and int(latency_fp.read_text()) <= 1)

    if combinational:
        logging.info(f"{design_name} schedules in one cycle, rebuilding as combinational")

        archive_run(design_build_dir, label="comb_chk_")

        gen_kernel_top(design, kernel, impl_spec, design_build_dir, combinational=True)
        gen_catapult_design_tcl(design, kernel, design_name, design_build_dir,
                                combinational=True)
        return_code = run_catapult(kernel_build_dir, design_build_dir)

    log_elapsed("Catapult", design_name, return_code, start_time)
    if return_code == 0:
        write_package(kernel, design, design_build_dir, combinational)
        logging.info(f"Catapult RTL packaged for {design_name}")


def dc_worker(design, kernel, kernel_path, kernel_build_dir, impl_spec, max_cores,
              dry_run=False):
    design_name = get_design_dir_name(design, kernel)
    design_build_dir = Path(kernel_build_dir, design_name)
    start_time = time.time()

    # A blackboxed dep was synthesized on its own, so the script links that
    # result rather than compiling the dep again
    entity = gen_dc_tcl(design, kernel, impl_spec, kernel_path, design_build_dir,
                        max_cores, dry_run)

    if dry_run:
        logging.info(f"  would run Design Compiler for {design_name}")
        return

    logging.info(f"Running Design Compiler for {design_name}")

    # Design Compiler writes its work directories into the current directory,
    # so it gets one of its own. Catapult's is left alone for a dc only run.
    archive_run(design_build_dir, dirs=("dc",))
    dc_dir = design_build_dir / "dc"
    dc_dir.mkdir(parents=True, exist_ok=True)

    log_path = design_build_dir / "dc.tessera.log"
    with log_path.open("w") as log:
        result = subprocess.run(
            ["dc_shell", "-f", str((design_build_dir / "dc.tcl").resolve())],
            cwd=dc_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    log_elapsed("Design Compiler", design_name, result.returncode, start_time)
    if result.returncode == 0:
        measured = {"area_dc": read_dc_area(design_build_dir),
                    "delay_dc": read_dc_delay(design_build_dir),
                    "power_dc": read_dc_power(design_build_dir, entity)}
        update_manifest(design_build_dir, **{k: v for k, v in measured.items() if v})


def gls_worker(design, kernel, kernel_build_dir, dry_run=False):
    design_name = get_design_dir_name(design, kernel)
    design_build_dir = Path(kernel_build_dir, design_name)
    start_time = time.time()

    conf = RunConfig.load()
    tech = conf.tech[design["tech_type"]]
    if not tech.lib_verilog:
        raise Exception(
            f"'{design['tech_type']}' has no lib_verilog, so its cells cannot be simulated")

    archive_run(design_build_dir, dirs=("gls",))
    gls_dir = design_build_dir / "gls"

    makefile, combinational = gen_gls_makefile(
        kernel, design_build_dir, gls_dir,
        str(Path(tech.lib_verilog).expanduser()), tech.lib_verilog_defines)

    if dry_run:
        logging.info(f"  would simulate the netlist for {design_name}")
        return

    kind = "combinational" if combinational else "sequential"
    logging.info(f"Running gate level simulation for {design_name} ({kind})")
    passed = run_gls(kernel, design_build_dir, gls_dir, makefile, conf.tools["questa"])

    log_elapsed("Gate level simulation", design_name, 0 if passed else 1, start_time)


def power_worker(design, kernel, kernel_build_dir, max_cores, dry_run=False):
    design_name = get_design_dir_name(design, kernel)
    design_build_dir = Path(kernel_build_dir, design_name)
    start_time = time.time()

    # TODO: combinational kernel have an issue with PrimePower, needs to be fixed
    manifest = yaml.safe_load(
        Path(design_build_dir, "package", "manifest.yaml").read_text())
    if manifest["combinational"]:
        logging.info(f"  {design_name} is combinational, so its power is not measured")
        return

    archive_run(design_build_dir, dirs=("power",))
    power_dir = design_build_dir / "power"
    gen_power_tcl(design, kernel, design_build_dir, power_dir, max_cores)

    if dry_run:
        logging.info(f"  would measure power for {design_name}")
        return

    logging.info(f"Running PrimePower for {design_name}")

    # pt_shell reports PT-063 at startup, because this install has no Library
    # Compiler beside it. It reads the compiled library regardless.
    pt_shell = Path(RunConfig.load().tools["prime"]).expanduser() / "bin" / "pt_shell"

    log_path = design_build_dir / "power.tessera.log"
    with log_path.open("w") as log:
        result = subprocess.run(
            [str(pt_shell), "-f", str((design_build_dir / "power.tcl").resolve())],
            cwd=power_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    log_elapsed("PrimePower", design_name, result.returncode, start_time)
    if result.returncode == 0:
        power = read_power(power_dir)
        update_manifest(design_build_dir, power=power)
        logging.info(f"  {design_name} uses {power['total'] * 1e6:.1f} uW")


def run_catapult_flow(kernel, designs, sweep_flags, root_dir, threads,
                      threads_per_process, num_workers, dry_run=False):
    "Generate one kernel's sources and run the high level synthesis over them"
    kernel_path = find_kernel(kernel)
    kernel_build_dir = Path(BUILD_DIR, kernel)
    kernel_build_dir.mkdir(parents=True, exist_ok=True)
    impl_spec = read_impl_spec(kernel, kernel_path)

    logging.info(f"Generating kernel files for {kernel}")
    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(partial(gen_kernel_files, kernel=kernel,
                              kernel_path=kernel_path,
                              kernel_build_dir=kernel_build_dir,
                              impl_spec=impl_spec, sweep_flags=sweep_flags,
                              dry_run=dry_run),
                      designs))

    gen_catapult_kernel_tcl(sweep_flags, kernel, kernel_path, kernel_build_dir,
                            root_dir, threads_per_process)
    if dry_run:
        logging.info(f"  would run Catapult for {len(designs)} designs")
        return

    run_flow("Catapult", partial(catapult_worker, kernel=kernel,
                                  kernel_build_dir=kernel_build_dir,
                                  impl_spec=impl_spec),
              designs, num_workers, license="catapult_ultra")


def run_dc_flow(kernel, designs, threads_per_process, num_workers, dry_run):
    "Synthesize one kernel's designs, which its parents then link"
    kernel_path = find_kernel(kernel)
    run_flow("Design Compiler",
              partial(dc_worker, kernel=kernel,
                      kernel_path=kernel_path,
                      kernel_build_dir=Path(BUILD_DIR, kernel),
                      impl_spec=read_impl_spec(kernel, kernel_path),
                      max_cores=threads_per_process,
                      dry_run=dry_run),
              designs, num_workers, license="dc", dry_run=dry_run)


def run(kernel, threads, threads_per_process, sweep, run_only, dry_run, only, gui_mode):
    kernel_build_dir = Path(BUILD_DIR, kernel)
    flattened_path = kernel_build_dir / 'flattened_sweep_config.json'
    root_dir = Path(__file__).parent.parent

    # A flow on its own reuses what an earlier run built, so the design list
    # comes from that run rather than the sweep
    reuse = run_only or only
    assert not reuse or flattened_path.exists(), \
        f"--run-only and the --*-only flows reuse an existing build. " \
        f"Run without them first.\n  missing: {flattened_path}"

    kernel_conf = KernelConfig.load(find_kernel(kernel))
    kernel_build_dir.mkdir(parents=True, exist_ok=True)

    # The flags are settings, so they always come from the sweep file. Only
    # the designs are stored, since a rerun has to match what was built.
    sweep_conf = SweepConfig.load(sweep).model_dump()
    sweep_flags = sweep_conf['flags']

    if not reuse:
        flattened_sweep = flatten_sweep(sweep_conf['sweep'])
        flattened_path.write_text(json.dumps({'sweep': flattened_sweep}, indent=2))
    else:
        flattened_sweep = json.loads(Path(flattened_path).read_text())['sweep']

    num_workers = threads // threads_per_process

    logging.info(f"Running {len(flattened_sweep)} designs for {kernel}")
    logging.info(f"{num_workers} workers, {threads_per_process} threads each, "
                 f"{threads} total")

    logging.info(f"Flattened sweep designs:")
    for i, design in enumerate(flattened_sweep, 1):
        logging.info(f"  [{i}/{len(flattened_sweep)}] {get_design_dir_name(design, kernel)}")

    # automatic dependency resolution and scheduling
    schedule = resolve(kernel, flattened_sweep)
    log_schedule(schedule)

    # A flow the sweep did not ask for cannot run on its own
    flag = {"dc": "syn", "gls": "gls", "power": "power"}.get(only)
    if flag and not sweep_flags[flag]:
        logging.warning(f"--{only}-only was given, but {sweep} has {flag}: false, "
                        f"so no flow will run")

    # --- C++ Verification + Catapult HLS + HLS-generated RTL Verification with QuestaSim Flow ---
    if only in (None, "catapult"):
        # We build each dependent kernel sequentially in topological order.
        # But all designs for a kernel are built in parallel.
        for dep_kernel, dep_designs in schedule:
            # The parent kernel always rebuilt, since that is the request.
            # For dependent kernels we check if its already built and reuse.
            if dep_kernel != kernel:
                dep_designs = to_build(dep_kernel, dep_designs, "catapult")
            if dep_designs:
                run_catapult_flow(dep_kernel, dep_designs, sweep_flags, root_dir,
                                   threads, threads_per_process, num_workers, dry_run)

    # The flows below read what Catapult packaged, so a dry run of the whole
    # sweep stops here. Asking for one of them on its own still generates it.
    if dry_run and not only:
        return

    # --- Logic Synthesis with Design Compiler ---
    if sweep_flags['syn'] and only in (None, "dc"):
        flattened_sweep = select_designs(flattened_sweep, kernel, kernel_build_dir,
                                         sweep_flags['syn_sel'], kernel_conf.kernel_key)

        # Only the deps the surviving designs still use are worth synthesizing
        for dep_kernel, dep_designs in resolve(kernel, flattened_sweep):
            if dep_kernel != kernel:
                dep_designs = to_build(dep_kernel, dep_designs, "dc")
            if dep_designs:
                run_dc_flow(dep_kernel, dep_designs, threads_per_process,
                             num_workers, dry_run)

    # --- Gate Level Simulation with QuestaSim ---
    if sweep_flags['gls'] and only in (None, "gls"):
        run_flow("gate level simulation", partial(gls_worker, kernel=kernel,
                                                   kernel_build_dir=kernel_build_dir,
                                                   dry_run=dry_run),
                  flattened_sweep, num_workers, dry_run=dry_run)

    # --- Power Analysis Flow with PrimePower ---
    if sweep_flags['power'] and only in (None, "power"):
        run_flow("PrimePower", partial(power_worker, kernel=kernel,
                                       kernel_build_dir=kernel_build_dir,
                                       max_cores=threads_per_process,
                                       dry_run=dry_run),
                  flattened_sweep, num_workers, license="prime_power", dry_run=dry_run)

