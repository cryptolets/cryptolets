from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import replace
import json
import logging

from tessera.models import KernelContext, RunConfig, SweepConfig
from tessera.helper import (get_design_dir_name, 
                            get_license_info,
                            mark_done,
                            watch_memory)
from tessera.kernel import find_kernel
from tessera.parser.cpp import parse_header
from tessera.sweep import flatten_sweep
from tessera.schedule import get_schedule
from tessera.const import BUILD_DIR, FLATTENED_SWEEP_FILE, ROOT_DIR
from tessera.flows import FLOWS, STAGES, has_stage

def run_flow(flow, designs, kernel_ctx):
    "Pool one flow over a kernel's designs, and report how many passed"

    # If a flow doesn't support multi-threading it uses 1 thread per worker
    # Instead of hogging multiple threads per worker.
    workers = kernel_ctx.workers if flow.multi_threaded else kernel_ctx.threads

    if flow.license:
        available = get_license_info(flow.license)['available']
        logging.info(f"{available} {flow.name} licenses available")
        if available < workers:
            logging.warning(f"Not enough {flow.name} licenses available, "
                            f"using {available} workers")
        workers = min(workers, available)

    logging.info(f"Running {flow.name} for {kernel_ctx.kernel}")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda d: flow.run(d, kernel_ctx), designs))

    for design, ok in zip(designs, results):
        if ok:
            mark_done(kernel_ctx.kernel, design, flow.stage)

    # A worker that stops early reports nothing, so it did not pass
    if results:
        passed, total = sum(bool(r) for r in results), len(results)
        logging.info(f"{flow.name} Success Rate: {passed}/{total} "
                     f"({100*passed/total:.0f}%)")


def run(kernel, threads, threads_per_process, sweep, frm, to, only):
    logging.info(f"Running Tessera")
    kernel_build_dir = Path(BUILD_DIR, kernel)
    flattened_path = kernel_build_dir / FLATTENED_SWEEP_FILE

    # One stage names both ends of the range
    if only:
        frm = to = only

    # A run that starts past the first stage reuses what an earlier one built,
    # so the design list comes from that run rather than the sweep
    reuse_flattened_sweep = frm != STAGES[0]
    assert not reuse_flattened_sweep or flattened_path.exists(), \
        f"A run starting at {frm} reuses an existing build. Start at " \
        f"{STAGES[0]} first.\n  missing: {flattened_path}"

    kernel_build_dir.mkdir(parents=True, exist_ok=True)

    # The flags are settings, so they always come from the sweep file. Only
    # the designs are stored, since a rerun has to match what was built.
    sweep_conf = SweepConfig.load(sweep).model_dump()
    sweep_flags = sweep_conf['flags']

    if reuse_flattened_sweep:
        flattened_sweep = json.loads(Path(flattened_path).read_text())['sweep']
    else:
        flattened_sweep = flatten_sweep(sweep_conf['sweep'])
        flattened_path.write_text(json.dumps({'sweep': flattened_sweep}, indent=2))

    num_workers = threads // threads_per_process
    logging.info(f"Running {len(flattened_sweep)} designs for {kernel}")
    logging.info(f"{num_workers} workers, {threads_per_process} threads each, "
                 f"{threads} total")

    logging.info(f"Flattened sweep designs:")
    for i, design in enumerate(flattened_sweep, 1):
        logging.info(f"  [{i}/{len(flattened_sweep)}] {get_design_dir_name(design, kernel)}")

    # automatic dependency resolution and scheduling
    schedule = get_schedule(kernel, flattened_sweep)
    return
    if len(schedule) > 1:
        logging.info("Parent kernel requires resolving the following dependencies in order:")
        for cur_kernel, cur_designs in schedule:
            logging.info(f"  {cur_kernel}: {len(cur_designs)} designs")

    base_ctx = KernelContext(
        root_dir=ROOT_DIR,
        sweep_flags=sweep_flags,
        threads=threads,
        threads_per_process=threads_per_process,
        workers=num_workers,
        frm=frm,
        to=to,
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


    flows_to_run = [flow for flow in FLOWS if has_stage(flow.stage, frm, to)]

    # A dependency is built before the kernel that blackboxes it, so each
    # kernel goes through every flow before the next one starts.
    for cur_kernel, cur_designs in schedule:
        cur_path = find_kernel(cur_kernel)
        kernel_ctx = replace(
            base_ctx,
            kernel_name=cur_kernel,
            kernel_path=cur_path,
            kernel_build_dir=Path(BUILD_DIR, cur_kernel),
            impl_spec=parse_header(cur_path / 'impl' / f"{cur_kernel}_impl.h")
        )

        for flow in flows_to_run:
            designs = flow.designs(cur_designs, kernel_ctx)
            run_flow(flow, designs, kernel_ctx)

    stop.set()
