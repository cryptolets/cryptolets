"""
Point a kernel's dependencies at packaged RTL rather than their own C++.

The generated header shadows the dep's implementation under synthesis, so
Catapult wires in what that dep already built.
"""
import re
import shutil
from pathlib import Path

from tessera.deps import (blackboxed_deps, dep_design, dep_entity,
                          find_package)
from tessera.helper import get_design_dir_name, is_done
from tessera.kernel import find_kernel
from tessera.parser.cpp import parse_header
from tessera.steps.generate.codegen import to_macro
from tessera.templating import render


def package_rtl(rtl, kernel, entity, include_dir):
    "Copy the package's RTL in, named for this dep rather than its kernel"
    named = re.sub(rf"\b{kernel}(_[a-zA-Z0-9_]+)?\b",
                   lambda m: f"{entity}{m[1] or ''}", Path(rtl).read_text())
    out = Path(include_dir, f"{entity}.v")
    out.write_text(named)
    return out


def blackbox_variant(dep, manifest, rtl, impl_spec):
    "One packaged design, as the specialization that stands in for it"
    # Catapult splits a sequential port into its data and its handshake, and
    # names both after the parameter, so the RTL says which are outputs
    outputs = [p["name"] for p in manifest["ports"] if p["dir"] == "output"
               and p["name"] not in ("clk", "rst")]

    return {
        "args": to_macro(dep["args"]),
        "entity": dep["entity"],
        "rtl": str(rtl.resolve()),
        # The stub stands in for one instantiation, so its widths are the
        # design's own rather than the implementation's parameters
        "params": [{**p, "type": to_macro(p["type"])}
                   for p in impl_spec["params"]],
        "widths": {n: to_macro(e) for n, e in impl_spec["widths"].items()},
        "outputs": " ".join(outputs),
        "area": manifest["area"],
        "timing": (f'.delay({manifest["delay"]})' if manifest["combinational"]
                   else f'.clock_name("clk").latency({manifest["latency"]})'
                        f'.init_delay(1)'),
    }


def gen_blackbox_header(kernel, variants, impl_header, include_dir):
    "Write one header for a kernel, holding every packaged design of it"
    impl_spec = parse_kernel(impl_header)
    render(
        "blackbox.h.j2",
        Path(include_dir, f"{kernel}_impl.h"),
        kernel=kernel,
        impl=str(Path(impl_header).resolve()),
        template_decl=impl_spec["template_decl"],
        variants=variants,
    )


def gen_blackbox_headers(design, kernel_path, impl_spec, design_build_dir,
                         deps_unbuilt=False):
    "Write a header per blackboxed dep, and name the deps that got one"
    # Find the deps that are blackboxed defined in kernel.yaml
    blackboxed = blackboxed_deps(kernel_path, impl_spec, design['tech_type'])

    # A stale header from an earlier run would keep standing in for a dep that
    # is now inlined.
    include_dir = design_build_dir / "blackbox"
    shutil.rmtree(include_dir, ignore_errors=True)
    if not blackboxed:
        return []

    include_dir.mkdir(parents=True, exist_ok=True)
    build_root = Path(design_build_dir).parent.parent

    # A kernel gets one header, holding every packaged design of it, since a
    # parent can instantiate the same kernel at different arguments
    variants = {}
    for dep in blackboxed:
        # A gen only run has not built the deps yet, so it leaves a note of
        # what is missing rather than a header
        if deps_unbuilt and not is_done(dep["kernel"], dep_design(dep, design),
                                        "hls", build_root):
            render("blackbox_todo.h.j2",
                   Path(include_dir, f"{dep['kernel']}_impl.h"),
                   kernel=dep["kernel"],
                   manifest=Path(build_root, dep["kernel"],
                                 get_design_dir_name(dep_design(dep, design), dep["kernel"]),
                                 "package", "manifest.yaml"))
            continue

        dep = {**dep, "entity": dep_entity(dep, design)}
        package_dir, manifest = find_package(dep, design, build_root)
        impl = Path(find_kernel(dep["kernel"]), "impl", f"{dep['kernel']}_impl.h")
        rtl = package_rtl(package_dir / manifest["rtl"], dep["kernel"],
                          dep["entity"], include_dir)

        variants.setdefault(dep["kernel"], (impl, []))[1].append(
            blackbox_variant(dep, manifest, rtl, parse_kernel(impl)))

    for kernel, (impl, group) in variants.items():
        # Two designs that compute the same thing share a name, so the kernel
        # has to say what makes them different
        if len({v["entity"] for v in group}) != len(group):
            raise Exception(
                f"'{kernel}' is blackboxed more than once with the same name. "
                f"Add what differs to its kernel_key in kernel.yaml.")
        gen_blackbox_header(kernel, group, impl, include_dir)

    return blackboxed
