"""
Functions for dependency resolution and scheduling a kernel sweep.

Build a dependency graph for a kernel sweep with topological order
to determine the build order of children and parent kernels.
"""
import logging
from graphlib import TopologicalSorter
from pathlib import Path

from tessera.parser.cpp import parse_kernel_impl
from tessera.kernel import find_kernel
from tessera.models import KernelConfig


def get_all_kernel_deps(kernel):
    kernel_path = find_kernel(kernel)
    kernel_impl = parse_kernel_impl(Path(kernel_path, 'impl', f"{kernel}_impl.h"))
    dep_kernels_in_impl = set()

    def dfs(impl):
        for field_decl in impl["field_decls"]:
            if field_decl["decl_type"] == "template_type" and \
                field_decl["tmpl_name"].endswith("_impl"):
                dep_kernel = field_decl["tmpl_name"].replace("_impl", "")
                dep_kernels_in_impl.add(dep_kernel)

        for dep in impl['deps'].values():
            dfs(dep)

    dfs(kernel_impl)
    return dep_kernels_in_impl


def blackboxed_deps(kernel):
    """
    Return the list of blackboxed dependencies for a kernel.
    """
    blackboxed_deps_ls = KernelConfig.load(find_kernel(kernel)).blackbox
    dep_kernels_in_impl = get_all_kernel_deps(kernel)
    final_ls = set()

    for dep_kernel_name in blackboxed_deps_ls:
        if dep_kernel_name not in dep_kernels_in_impl:
            find_kernel(dep_kernel_name)
            logging.warning(f"Blackboxed dep '{dep_kernel_name}' is not in the impl")
        else:
            final_ls.add(dep_kernel_name)

    return final_ls


def resolve_kernels(kernel_graph, kernel):
    "resolve the kernel dependency graph"
    if kernel in kernel_graph:
        return

    kernel_graph[kernel] = blackboxed_deps(kernel)
    for dep in kernel_graph[kernel]:
        resolve_kernels(kernel_graph, dep)


def get_schedule(kernel, designs):
    """
    First, we need to resolve kernel-level dependency graph
    Then, we resolve which designs are needed for each kernel
    """
    # First, we need to resolve kernel-level dependency graph
    kernel_graph = {}
    resolve_kernels(kernel_graph, kernel)
    kernel_order = list(TopologicalSorter(kernel_graph).static_order())
    kernel_designs_map = {k: [] for k in kernel_order}

    print(kernel_order)


    # graph, needed = {}, {}
    # resolve_designs(kernel, designs, graph, needed)

    # order = TopologicalSorter(graph).static_order()
    # return [(k, list(needed[k].values())) for k in order]


# def resolve_kernels(kernel_graph, kernel):
#     if kernel in kernel_graph:
#         return kernel_graph

#     kernel_path = find_kernel(kernel)
#     impl_spec = parse_header(kernel_path / "impl" / f"{kernel}_impl.h")
    
#     deps = {d["kernel"] for d in blackboxed_deps(kernel_path, impl_spec)}

#     kernel_graph[kernel] = deps
#     for dep in deps:
#         resolve_kernels(kernel_graph, dep)
#     return kernel_graph