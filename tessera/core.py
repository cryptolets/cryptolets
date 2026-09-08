import threading
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from tessera.models.config import RunConfig

from tessera.models.sweep import SweepConfig
from tessera.models.run import Run
from tessera.helpers.license import get_license_info
from tessera.helpers.memory import watch_memory
from tessera.sweep import flatten_sweep
from tessera.schedule import get_schedule
from tessera.const import BUILD_DIR, FLATTENED_SWEEP_FILE, ROOT_DIR
from tessera.steps import PIPELINE, STAGES, has_stage

def run_step(step, designs, kernel, run):
    "Pool one step over a kernel's designs, and report how many passed"

    # If a step doesn't support multi-threading it uses 1 thread per worker
    # Instead of hogging multiple threads per worker.
    workers = run.workers if step.multi_threaded else run.threads

    if step.license:
        available = get_license_info(step.license)['available']
        logging.info(f"{available} {step.name} licenses available")
        if available < workers:
            logging.warning(f"Not enough {step.name} licenses available, "
                            f"using {available} workers")
        workers = min(workers, available)

    logging.info(f"Running {step.name} for {kernel.name}")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda d: step.run_wrapper(d, kernel, run), designs))

    for design, ok in zip(designs, results):
        if ok:
            step.mark_done(design)

    # A worker that stops early reports nothing, so it did not pass
    passed, total = sum(bool(r) for r in results), len(results)
    if total:
        logging.info(f"{step.name} Success Rate: {rate(passed, total)}")
    return passed, total


def rate(passed, total):
    return f"{passed}/{total} ({100 * passed / total:.0f}%)"


def run(kernel, threads, threads_per_process, sweep, frm, to, only):
    logging.info(f"Running Tessera")
    kernel_build_dir = Path(BUILD_DIR, kernel)
    flattened_sweep_path = kernel_build_dir / FLATTENED_SWEEP_FILE

    # One stage names both ends of the range
    if only: frm = to = only
    kernel_build_dir.mkdir(parents=True, exist_ok=True)

    # The flags are settings, so they always come from the sweep file. Only
    # the designs are stored, since a rerun has to match what was built.
    sweep_conf = SweepConfig.load(sweep)
    sweep_conf_map = sweep_conf.model_dump()
    sweep_flags = sweep_conf_map['flags']


    # Flatten the sweep, and reuse stored flattened sweep if
    # the generate (first) stage is skipped
    flattened_sweep = flatten_sweep(
        sweep_conf_map['sweep'], 
        flattened_sweep_path,
        reuse=frm != STAGES[0]
    )

    num_workers = threads // threads_per_process
    logging.info(f"Running {len(flattened_sweep)} designs for {kernel}")
    logging.info(f"{num_workers} workers, {threads_per_process} threads each, "
                 f"{threads} total")

    logging.info(f"Flattened sweep designs:")
    for i, design in enumerate(flattened_sweep, 1):
        logging.debug(f"  [{i}/{len(flattened_sweep)}] {design.get_name()}")

    # automatic dependency resolution and scheduling
    schedule = get_schedule(kernel, flattened_sweep)
    if len(schedule) > 1:
        logging.info("Parent kernel requires resolving the following dependencies in order:")
        for cur_kernel, cur_designs in schedule:
            logging.info(f"  {cur_kernel.name}: {len(cur_designs)} designs")

    run_inst = Run(
        target=kernel,
        threads=threads,
        threads_per_process=threads_per_process,
        workers=num_workers,
        sweep_flags=sweep_flags,
        frm=frm,
        to=to,
        root_dir=ROOT_DIR,
    )

    # Warn if HLS RTL verification is skipped when HLS was generated
    if has_stage("hls", frm, to) and not has_stage("rtl", frm, to):
        logging.warning("SKIPPING RTL Verification")

    # C++ and RTL verification flows are embedded in the Catapult run
    # so they cannot be run without HLS flow
    for stage in ("cpp", "rtl"):
        if has_stage(stage, frm, to) and not has_stage("hls", frm, to):
            logging.warning(f"{stage} cannot be run without HLS flow")

    # An unblackboxed design can grow until the machine has nothing left
    stop = threading.Event()
    threading.Thread(target=watch_memory, daemon=True,
                     args=(stop, RunConfig.load().min_free_gb)).start()

    steps_to_run = [step for step in PIPELINE
                    if any(has_stage(s, frm, to) for s in step.stages)]

    # Main loop to run steps for each kernel and designs
    summary = {}
    for cur_kernel, cur_designs in schedule:
        for step in steps_to_run:
            step.setup(cur_kernel, cur_designs, run_inst)
            designs = step.designs(cur_designs, cur_kernel, run_inst)
            summary[cur_kernel.name, step.name] = run_step(step, designs, cur_kernel, run_inst)

    stop.set()

    # Kernels in build order, steps in pipeline order, as they ran
    logging.info("Summary:")
    for cur_kernel, _ in schedule:
        logging.info(f"  {cur_kernel.name}:")
        for step in steps_to_run:
            passed, total = summary[cur_kernel.name, step.name]
            logging.info(f"    {step.name}: {rate(passed, total) if total else 'no designs'}")
