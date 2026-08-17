"""
Work out which kernels a sweep needs, and in what order.

A blackboxed dep is a design of its own, built at its own width and period, and
the parent needs it packaged before it can run. Resolving that gives the kernels
in build order, each with the exact designs the parents asked for.
"""
import logging
from graphlib import TopologicalSorter
from pathlib import Path

from tessera.blackbox import blackboxed_deps, dep_design
from tessera.codegen import read_impl_spec
from tessera.helper import get_design_dir_name
from tessera.kernel import find_kernel

BUILD_DIR = Path('build')


def resolve(kernel, designs):
    """
    The kernels this sweep needs, deepest first, as [(kernel, designs), ...].

    A kernel appears once, holding every design any parent asked of it, so a
    dep two parents share is built one time.
    """
    graph, needed = {}, {}
    _walk(kernel, designs, graph, needed)

    order = TopologicalSorter(graph).static_order()
    return [(k, list(needed[k].values())) for k in order]


def _walk(kernel, designs, graph, needed):
    "Record what this kernel needs, then do the same for its blackboxed deps"
    seen = needed.setdefault(kernel, {})
    fresh = [d for d in designs if get_design_dir_name(d) not in seen]
    for design in fresh:
        seen[get_design_dir_name(design)] = design

    kernel_path = find_kernel(kernel)
    tech_type = designs[0]["tech_type"] if designs else None
    deps = blackboxed_deps(kernel_path, read_impl_spec(kernel, kernel_path), tech_type)
    graph.setdefault(kernel, set()).update(dep["kernel"] for dep in deps)

    # Only the designs new to this kernel can ask for a dep design not seen yet
    for dep in deps:
        if fresh:
            _walk(dep["kernel"], [dep_design(dep, d) for d in fresh], graph, needed)


def unbuilt(kernel, designs, product):
    """
    The designs a phase still has to build, given what it produces.

    A dep shared by several parents, or one an earlier run already built, is
    finished. Building it again would only reproduce the file its parents read.
    """
    todo, done = [], []
    for design in designs:
        path = Path(BUILD_DIR, kernel, get_design_dir_name(design), product)
        (done if path.exists() else todo).append(design)

    if done:
        logging.info(f"{kernel}: {len(done)} of {len(designs)} designs already built")

    return todo


def log_schedule(schedule):
    "Say what will be built, since a sweep of one kernel can need several"
    if len(schedule) < 2:
        return

    logging.info("Kernels this sweep needs, in build order:")
    for kernel, designs in schedule:
        logging.info(f"  {kernel}: {len(designs)} designs")
