"""
Which kernels to build, in what order, and which designs of each.

A kernel's blackboxed deps come from its kernel.yaml. Which designs of a dep
a parent design needs comes from the compiler, since the parent's impl picks
its children with `if constexpr` on the design's parameters.
"""
import logging
from graphlib import TopologicalSorter

from tessera.const import HW_CONSTRAINTS_PARAMS
from tessera.models.design import Design, PARAMS_MAPPED_TO_STRUCT
from tessera.models.kernel import Kernel
from tessera.parser.cpp import live_instances


def resolve_kernels(kernels, kernel_name):
    "Load a kernel and, recursively, the kernels it blackboxes"
    if kernel_name in kernels:
        return
    kernels[kernel_name] = Kernel(kernel_name)
    for dep in kernels[kernel_name].config.blackbox:
        resolve_kernels(kernels, dep)


def child_design(parent, params, child_kernel):
    """
    A child design: the parent's values for the child's design key, then
    the template arguments the compiler gave the child, then the hardware
    constraints, which a child inherits.
    """
    design = {k: parent.design[k] for k in child_kernel.config.design_key
              if k in parent.design}
    design.update(params)

    for param in HW_CONSTRAINTS_PARAMS:
        design[param] = parent.design[param]
    design["period"] = parent.design["dep_period_ratio"] * parent.design["period"]

    child = Design(design)
    # The parent already holds the structs the child's refs point at
    for param in PARAMS_MAPPED_TO_STRUCT:
        root = design.get(param, "").split("-")[0]
        if root in parent.structs:
            child.structs[root] = parent.structs[root]
    return child


def resolve_designs(parent_kernel, parent_designs, kernels, kernel_designs):
    "Add the child designs each parent design instantiates, deduplicated"
    for parent in parent_designs.values():
        instances = live_instances(parent, parent_kernel)

        for child_name in parent_kernel.config.blackbox:
            if child_name not in instances:
                logging.warning(f"{parent_kernel.name} {parent.build_dir.name} "
                                f"does not use blackboxed dep '{child_name}'")
                continue

            child_kernel = kernels[child_name]
            for params in instances[child_name]:
                child = child_design(parent, params, child_kernel)
                key = child.get_hash(child_kernel.config.design_key)
                child = kernel_designs[child_name].setdefault(key, child)
                parent.deps.setdefault(child_name, {})[key] = child


def get_schedule(kernel_name: str, designs: list[Design]):
    "The kernels in build order, each with the designs it needs"
    kernels = {}
    resolve_kernels(kernels, kernel_name)
    graph = {name: kernel.config.blackbox for name, kernel in kernels.items()}
    order = list(TopologicalSorter(graph).static_order())

    # name -> hash -> Design, so each kernel holds a design once
    kernel_designs = {name: {} for name in order}
    design_key = kernels[kernel_name].config.design_key
    kernel_designs[kernel_name] = {d.get_hash(design_key): d for d in designs}

    # Parents first, so a kernel's designs are complete before it passes
    # them down to its own deps
    for name in reversed(order):
        for design in kernel_designs[name].values():
            design.attach(kernels[name])
            design.uses_blackboxes = bool(graph[name])
        resolve_designs(kernels[name], kernel_designs[name], kernels, kernel_designs)

    return [(kernels[name], list(kernel_designs[name].values())) for name in order]
