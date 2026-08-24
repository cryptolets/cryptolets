"""
Point a kernel's dependencies at packaged RTL rather than their own C++.

The generated header shadows the dep's implementation under synthesis, so
Catapult wires in what that dep already built.
"""
import shutil
from pathlib import Path

from tessera.deps import blackboxed_deps, dep_design, find_package
from tessera.helper import get_design_dir_name, missing_products
from tessera.kernel import find_kernel
from tessera.parse import parse_kernel
from tessera.templating import render


def resolved_params(impl_spec, manifest):
    """
    The implementation's parameters, sized by the RTL that was built.

    A parameter's width is written as the implementation derives it, which
    only reads outside the implementation. The package records what each port
    came out as, so the widths are taken from there instead.
    """
    widths = {port["name"]: port["width"] for port in manifest["ports"]}
    params = []
    for param in impl_spec["params"]:
        signed = str(param["type"]).rstrip("> ").endswith("true")
        params.append({**param,
                       "type": f"ac_int<{widths[param['name']]}, "
                               f"{'true' if signed else 'false'}>"})
    return params


def gen_blackbox_header(kernel, manifest, rtl, impl_header, include_dir):
    """
    Generate the header file that blackboxes the package and branches
    pointing to the real implementation.
    """
    impl_spec = parse_kernel(impl_header)

    # Catapult splits a sequential port into its data and its handshake, and
    # names both after the parameter, so the RTL says which are outputs
    outputs = [p["name"] for p in manifest["ports"] if p["dir"] == "output"
               and p["name"] not in ("clk", "rst")]

    timing = (f'.delay({manifest["delay"]})' if manifest["combinational"] else
              f'.clock_name("clk").latency({manifest["latency"]}).init_delay(1)')

    render(
        "blackbox.h.j2",
        Path(include_dir, f"{kernel}_impl.h"),
        kernel=kernel,
        entity=manifest["entity"],
        rtl=str(Path(rtl).resolve()),
        impl=str(Path(impl_header).resolve()),
        template_decl=impl_spec["template_decl"],
        params=resolved_params(impl_spec, manifest),
        outputs=" ".join(outputs),
        area=manifest["area"],
        timing=timing,
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

    for dep in blackboxed:
        # When we gen only (dry run), we don't have the deps built yet, so we
        # need to check if they are missing. If they are missing, 
        # we use generate a placeholder header.
        if deps_unbuilt and missing_products(dep["kernel"], dep_design(dep, design),
                                        "hls", build_root):
            render("blackbox_todo.h.j2",
                   Path(include_dir, f"{dep['kernel']}_impl.h"),
                   kernel=dep["kernel"],
                   manifest=Path(build_root, dep["kernel"],
                                 get_design_dir_name(dep_design(dep, design), dep["kernel"]),
                                 "package", "manifest.yaml"))
            continue

        package_dir, manifest = find_package(dep, design, build_root)
        impl = Path(find_kernel(dep["kernel"]), "impl", f"{dep['kernel']}_impl.h")
        gen_blackbox_header(dep["kernel"], manifest,
                            package_dir / manifest["rtl"], impl, include_dir)

    return blackboxed
