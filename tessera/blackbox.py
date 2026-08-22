"""
Blackbox a kernel's dependencies with packaged RTL.

A dep is instantiated at its own width, so l0_int_sub<_FIELD::W+1> inside a
32 bit parent needs the 33 bit package. Each dep resolves to a package built
earlier in the sweep, and the generated header points Catapult at its RTL
instead of the implementation.
"""
import re
import shutil
from pathlib import Path

import yaml

from tessera.config import KernelConfig, curves, is_fpga
from tessera.helper import get_design_dir_name, missing_products, require_built
from tessera.kernel import find_kernel
from tessera.parse import parse_kernel
from tessera.templating import render


def dep_field(arg, design):
    "A field names a curve and one of its fields, so BN254_BASE gives both"
    if arg == "_FIELD":
        return {}  # the parent's own field, which the dep design already holds

    name = arg.lower()
    for curve, fields in curves().items():
        for field in ("base", "scalar"):
            if field in fields and name == f"{curve}_{field}":
                return {"curve": curve, "field": field}

    raise Exception(f"Cannot read dep field '{arg}'")


def dep_arg(arg, design):
    """
    What a dep's template argument sets, as {param: value}.

    A field sets the curve and the field together, anything else sets the one
    parameter it stands for.
    """
    if arg == "_FIELD" or re.fullmatch(r"[A-Za-z_]\w*_(base|scalar)", arg, re.I):
        return dep_field(arg, design)

    expr = re.sub(r"\b_FIELD::W\b|\b_BITWIDTH\b", str(design["bitwidth"]), arg).strip()
    if re.fullmatch(r"[A-Za-z_]\w*", expr):
        # A parameter of the parent passes its value on, named with the leading
        # underscore a template takes or without it. Anything else is an enum.
        name = expr.lower()
        return design.get(name, design.get(name.lstrip("_"), name))

    try:
        return eval(expr, {"__builtins__": {}})
    except Exception:
        raise Exception(f"Cannot read dep argument '{arg}'")


def dep_params(dep, design):
    "The parameters a dep's template arguments set, positional against its class"
    header = Path(find_kernel(dep["kernel"]), "impl", f"{dep['kernel']}_impl.h")
    names = [p.lstrip("_").lower() for p in parse_kernel(header)["template_params"]]

    args = [a for a in dep["args"].split(",") if a.strip()]
    if len(args) > len(names):
        raise Exception(
            f"'{dep['kernel']}' takes {len(names)} template parameters "
            f"({', '.join(names)}), but {dep['name']} gives {len(args)}")

    params = {}
    for name, arg in zip(names, args):
        value = dep_arg(arg, design)
        # A field argument names its own parameters, the rest set just theirs
        params.update(value if isinstance(value, dict) else {name: value})
    return params


def dep_design(dep, design):
    """
    The design a dep is packaged as.

    Its template arguments say how it differs from the parent, and it runs at a
    fraction of the parent's period so a chain of blackboxes fits its clock.
    """
    ratio = design.get("dep_period_ratio", 1)
    return {
        **design,
        **dep_params(dep, design),
        "period": round(design["period"] * ratio, 4),
    }


def blackboxed_deps(kernel_path, impl_spec, tech_type=None):
    """
    The deps this kernel reuses as packaged RTL, as the impl spec describes them.

    The kernel names which ones, so the rest are compiled into it and need no
    build of their own.
    """
    # TODO: support blackboxing on FPGA. Vivado synthesizes the whole design at
    # once, so a packaged dep would need an equivalent of the ASIC flow's ddc.
    if tech_type and is_fpga(tech_type):
        return []

    wanted = KernelConfig.load(kernel_path).blackbox
    unknown = set(wanted) - {dep["kernel"] for dep in impl_spec["deps"]}
    if unknown:
        raise Exception(
            f"'{impl_spec['name']}' does not use {', '.join(sorted(unknown))}, "
            f"so they cannot be blackboxed")

    return [dep for dep in impl_spec["deps"] if dep["kernel"] in wanted]


def find_package(dep, design, build_root):
    "The dep's package dir and manifest, or an error naming what is missing"
    wanted = dep_design(dep, design)
    require_built(dep["kernel"], wanted, "catapult", build_root)

    package_dir = Path(build_root, dep["kernel"],
                       get_design_dir_name(wanted, dep["kernel"]), "package")
    return package_dir, yaml.safe_load(Path(package_dir, "manifest.yaml").read_text())


def gen_blackbox_header(kernel, manifest, rtl, impl_header, include_dir):
    """
    Write the dep's header so it blackboxes the package under synthesis.

    Catapult names the RTL ports after the run parameters, so the parameters
    take the packaged module's port names. A mismatch is not reported, it
    just produces RTL that cannot be elaborated.
    """
    ports = [p for p in manifest["ports"] if p["name"] not in ("clk", "rst")]

    timing = (f'.delay({manifest["delay"]})' if manifest["combinational"] else
              f'.clock_name("clk").latency({manifest["latency"]}).init_delay(1)')

    render(
        "blackbox.h.j2",
        Path(include_dir, f"{kernel}_impl.h"),
        kernel=kernel,
        entity=manifest["entity"],
        rtl=str(Path(rtl).resolve()),
        impl=str(Path(impl_header).resolve()),
        ports=ports,
        outputs=" ".join(p["name"] for p in ports if p["dir"] == "output"),
        area=manifest["area"],
        timing=timing,
    )


def gen_blackbox_headers(design, kernel_path, impl_spec, design_build_dir, dry_run=False):
    "Generate a header and copy the RTL per dep, into a dir that shadows impl"
    blackboxed = blackboxed_deps(kernel_path, impl_spec, design['tech_type'])

    # The TCL blackboxes whatever this dir holds, so a stale one from an
    # earlier run would keep blackboxing a dep that is now inlined.
    include_dir = design_build_dir / "blackbox"
    shutil.rmtree(include_dir, ignore_errors=True)
    if not blackboxed:
        return

    include_dir.mkdir(parents=True, exist_ok=True)
    build_root = Path(design_build_dir).parent.parent

    for dep in blackboxed:
        # A dry run stops before the tool, so a dep it would have built is
        # named rather than described
        if dry_run and missing_products(dep["kernel"], dep_design(dep, design),
                                        "catapult", build_root):
            render("blackbox_todo.h.j2",
                   Path(include_dir, f"{dep['kernel']}_impl.h"),
                   kernel=dep["kernel"],
                   manifest=Path(build_root, dep["kernel"],
                                 get_design_dir_name(dep_design(dep, design), dep["kernel"]),
                                 "package", "manifest.yaml"))
            continue

        package_dir, manifest = find_package(dep, design, build_root)

        rtl = include_dir / manifest["rtl"]
        rtl.write_text(Path(package_dir, manifest["rtl"]).read_text())

        impl = Path(find_kernel(dep["kernel"]), "impl", f"{dep['kernel']}_impl.h")
        gen_blackbox_header(dep["kernel"], manifest, rtl, impl, include_dir)
