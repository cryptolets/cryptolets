"""
Functions for dependency resolution and scheduling a kernel sweep.

Build a dependency graph for a kernel sweep with topological order
to determine the build order of children and parent kernels.
"""
import logging
from graphlib import TopologicalSorter
from pathlib import Path

from tessera.deps import blackboxed_deps, dep_design
from tessera.parse import parse_impl_spec
from tessera.helper import get_design_dir_name, missing_products
from tessera.kernel import find_kernel

BUILD_DIR = Path('build')

def resolve(kernel, designs):
    """
    Main function which returns the topologial order scheduling 
    for kernels and its dependencies for the defined designs.
    """
    graph, needed = {}, {}
    _walk(kernel, designs, graph, needed)

    order = TopologicalSorter(graph).static_order()
    return [(k, list(needed[k].values())) for k in order]


def _walk(kernel, designs, graph, needed):
    seen = needed.setdefault(kernel, {})
    fresh = [d for d in designs if get_design_dir_name(d, kernel) not in seen]
    for design in fresh:
        seen[get_design_dir_name(design, kernel)] = design

    kernel_path = find_kernel(kernel)
    tech_type = designs[0]["tech_type"] if designs else None
    deps = blackboxed_deps(kernel_path, parse_impl_spec(kernel, kernel_path), tech_type)
    graph.setdefault(kernel, set()).update(dep["kernel"] for dep in deps)

    # Recursing on the new designs alone terminates the walk: a node revisited
    # with nothing new has nothing to pass down
    for dep in deps:
        if fresh:
            _walk(dep["kernel"], [dep_design(dep, d) for d in fresh], graph, needed)


def to_build(kernel, designs, flow):
    """
    Given a kernel's designs and the flow to run, return the designs still
    missing any of the files that flow produces.
    """
    todo, done = [], []
    for design in designs:
        target = todo if missing_products(kernel, design, flow) else done
        target.append(design)

    if done:
        logging.info(f"{kernel}: {len(done)} of {len(designs)} designs already built")

    return todo


def log_schedule(schedule):
    if len(schedule) < 2: return
    logging.info("Parent kernel requires resolving the following dependencies in order:")
    for kernel, designs in schedule:
        logging.info(f"  {kernel}: {len(designs)} designs")
