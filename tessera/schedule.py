"""
"""
import logging
from graphlib import TopologicalSorter
from simpleeval import simple_eval

from tessera.kernel import find_kernel
from tessera.const import HW_CONSTRAINTS_PARAMS
from tessera.models.design import Design
from tessera.models.kernel import Kernel
from tessera.models.sweep import get_sweep_enum_vars


def get_all_kernel_deps(kernel_impl):
    dep_kernels_in_impl = {}

    def dfs(impl):
        for field_decl in impl["field_decls"]:
            if field_decl["kernel"]:
                dep_kernel = field_decl["kernel"]
                if dep_kernel not in dep_kernels_in_impl:
                    dep_kernels_in_impl[dep_kernel] = []
                dep_kernels_in_impl[dep_kernel].append(field_decl["tmpl_params"])

        for dep in impl['deps'].values():
            dfs(dep)

    dfs(kernel_impl)
    return dep_kernels_in_impl


def get_blackboxed_deps(kernel):
    """
    Return the blackboxed dependencies of a kernel, with their inst args.
    """
    dep_kernels_in_impl = get_all_kernel_deps(kernel.impl_spec)
    dep_kernel_tmpl_params_map = {}

    for dep_kernel_name in kernel.config.blackbox:
        if dep_kernel_name not in dep_kernels_in_impl:
            find_kernel(dep_kernel_name) # errors on a typo
            logging.warning(f"Blackboxed dep '{dep_kernel_name}' is not in the impl")
        else:
            dep_kernel_tmpl_params_map[dep_kernel_name] = dep_kernels_in_impl[dep_kernel_name]

    return dep_kernel_tmpl_params_map


def resolve_kernels(kernels, kernel_graph, kernel_name):
    """
    Resolve the kernel dependency graph
    """
    if kernel_name in kernels:
        return

    kernels[kernel_name] = Kernel(kernel_name)
    kernel_graph[kernel_name] = get_blackboxed_deps(kernels[kernel_name])

    for dep in kernel_graph[kernel_name]:
        resolve_kernels(kernels, kernel_graph, dep)


def resolve_designs(
    parent_kernel, parent_inst_args, parent_designs, parent_sweep_params,
    child_kernel
):
    """
    Resolves the child's designs
    """
    child_tmpl_params = child_kernel.impl_spec["tmpl_params"]

    child_designs = []
    # TODO: we can multithread this, if it becomes a bottleneck
    #       because there can be lots of designs
    for design in parent_designs:
        expr_vars = {**get_sweep_enum_vars(), **design.get_expr_vars()}

        for parent_inst in parent_inst_args:
            child_design = {}
            num_child_params = len(child_tmpl_params)
            num_parent_inst_params = len(parent_inst)

            for i in range(num_child_params):
                param = child_tmpl_params[i]["name"]
                default = child_tmpl_params[i]["default"]

                if i < num_parent_inst_params:
                    # If the parent defines the child param in its inst args
                    # We have to use it, and resolve the var and/or expression
                    arg = parent_inst[i]

                    if child_tmpl_params[i]["type"] == "class":
                        # The child tmpl wants a struct: the child's param, named by
                        # the child tmpl, holds a reference to it.
                        if arg["kind"] == "name":
                            root, path = arg["name"], []
                        elif arg["kind"] == "qual":
                            root, path = arg["parts"][0], arg["parts"][1:]
                        else:
                            raise Exception(f"'{child_kernel.name}' wants a struct "
                                            f"for '{param}', got '{arg['text']}'")

                        # The parent's own params resolve to what they hold
                        if arg["is_tmpl_param"]:
                            root = design.design[root]
                        child_design[param] = "-".join([root, *path])
                    else:
                        # The parent inst arg is an expression, a design param,
                        # an enum value, or a struct member, all resolved by eval
                        if arg["kind"] == "expr":
                            text = arg["text"]
                        elif arg["kind"] == "name":
                            text = arg["name"]
                        else:
                            text = "__".join(arg["parts"])
                        child_design[param] = simple_eval(text, names=expr_vars)
                elif param in design.design:
                    # If parent doesn't define the child param in its inst args
                    # fallback to using the parent's design params
                    child_design[param] = design.design[param]
                elif default:
                    # If the child has a default value that is not
                    # the param itself, we use the default.
                    child_design[param] = default
                else:
                    raise Exception(
                        f"'{child_kernel.name}' needs '{param}', but "
                        f"'{parent_kernel.name}' design has no value for it")

            # resolving hardware constraints for child
            for param in HW_CONSTRAINTS_PARAMS:
                if param == "period":
                    # Child's period is the ratio of the parent's period
                    child_design[param] = design.design["dep_period_ratio"] * design.design["period"]
                else:
                    child_design[param] = design.design[param]

            child_designs.append(Design(child_design))

    return child_designs


def get_schedule(kernel_name: str, designs: list[Design], sweep_params: dict):
    """
    First, resolve the kernel-level dependency graph.
    Then, resolve which designs are needed for each kernel.
    Finaly, returns list of kernels in build order and their designs
    """
    # kernels: name -> Kernel; kernel_graph: name -> dep name -> inst args
    kernels, kernel_graph = {}, {}
    resolve_kernels(kernels, kernel_graph, kernel_name)
    kernel_order = list(TopologicalSorter(kernel_graph).static_order())

    kernel_designs_map = {k: [] for k in kernel_order}
    kernel_designs_map[kernel_name] = designs

    sweep_params_map = {k: [] for k in kernel_order}
    sweep_params_map[kernel_name] = sweep_params

    # Parents first, so a kernel's designs are complete before it passes
    # them down to its own deps
    for parent_name in reversed(kernel_order):
        for design in kernel_designs_map[parent_name]:
            design.attach_structs(kernels[parent_name])

        for child_name in kernel_graph[parent_name]:
            kernel_designs_map[child_name] += resolve_designs(
                parent_kernel=kernels[parent_name],
                parent_inst_args=kernel_graph[parent_name][child_name],
                parent_designs=kernel_designs_map[parent_name],
                parent_sweep_params=sweep_params_map[parent_name],
                child_kernel=kernels[child_name],
            )

    # Deduplicate designs
    for name in kernel_order:
        design_key = kernels[name].config.design_key
        unique = {d.get_hash(design_key): d for d in kernel_designs_map[name]}
        kernel_designs_map[name] = list(unique.values())

    return [(kernels[k], kernel_designs_map[k]) for k in kernel_order]
