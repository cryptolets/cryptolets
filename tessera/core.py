from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import logging

from tessera.config import SweepConfig
from tessera.helper import get_design_dir_name, get_license_info
from tessera.kernel import find_kernel
from tessera.parse import parse_impl_spec
from tessera.sweep import flatten_sweep
from tessera.schedule import resolve, log_schedule, to_build, BUILD_DIR
from tessera.flows import FLOWS, STAGES, KernelContext, has_stage

def run_flow(flow, designs, kernel_ctx):
    "Pool one flow over a kernel's designs, and report how many passed"
    # Catapult holds one thread per process, so it takes every worker
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

    # A worker that stops early reports nothing, so it did not pass
    if results:
        passed, total = sum(bool(r) for r in results), len(results)
        logging.info(f"{flow.name} Success Rate: {passed}/{total} "
                     f"({100*passed/total:.0f}%)")


def run(kernel, threads, threads_per_process, sweep, frm, to, only):
    kernel_build_dir = Path(BUILD_DIR, kernel)
    flattened_path = kernel_build_dir / 'flattened_sweep_config.json'
    root_dir = Path(__file__).parent.parent

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
    schedule = resolve(kernel, flattened_sweep)
    log_schedule(schedule)

    kernel_ctx = KernelContext(
        parent=kernel,
        root_dir=root_dir,
        sweep_flags=sweep_flags,
        threads=threads,
        threads_per_process=threads_per_process,
        workers=num_workers,
        frm=frm,
        to=to,
    )

    # Warn if HLS RTL verification is skipped when HLS was generated
    if has_stage("hls", frm, to) and not has_stage("rtl", frm, to):
        logging.warning("SKIPPING rtl verification")

    # And verification without it has nothing to check, since both run inside
    # the Catapult run rather than on their own
    for stage in ("cpp", "rtl"):
        if has_stage(stage, frm, to) and not has_stage("hls", frm, to):
            logging.warning(f"{stage} verification cannot be run without HLS flow")

    # A dependency is built before the kernel that blackboxes it, so each
    # kernel goes through every flow before the next one starts.
    for dep_kernel, dep_designs in schedule:
        dep_path = find_kernel(dep_kernel)
        kernel_ctx = replace(kernel_ctx, kernel=dep_kernel, kernel_path=dep_path,
                      kernel_build_dir=Path(BUILD_DIR, dep_kernel),
                      impl_spec=parse_impl_spec(dep_kernel, dep_path))

        for flow in FLOWS:
            if not has_stage(flow.stage, frm, to):
                continue

            designs = flow.designs(dep_designs, kernel_ctx)

            # The parent is always rebuilt, since that is the request. A
            # dependency is reused when it holds what this flow would write.
            if dep_kernel != kernel:
                designs = to_build(dep_kernel, designs, flow.stage)

            if designs:
                run_flow(flow, designs, kernel_ctx)
