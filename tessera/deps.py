"""
Helper functions for dependent kernels.
"""
import hashlib
import logging
import re
from pathlib import Path

import yaml

from tessera.models import KernelConfig, load_curves, is_fpga
from tessera.helper import get_design_dir_name, require_built
from tessera.kernel import find_kernel
from tessera.parser.cpp import parse_header


def dep_field(arg):
    "Special case parsing for field parameters"
    if arg == "_FIELD":
        return {}  # the parent's own field, which the dep design already holds

    name = arg.lower()
    for curve, fields in load_curves().items():
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
        return dep_field(arg)

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

def dep_entity(dep, design):
    """
    What a dep's top module is called inside its parent.

    A parent can hold the same kernel more than once, at different arguments,
    and each one is a different package. The name is taken from what the kernel
    computes, so two that compute the same thing are the same module.
    """
    wanted = dep_design(dep, design)
    keys = KernelConfig.load(find_kernel(dep["kernel"])).kernel_key
    named = "__".join(f"{k}_{wanted[k]}" for k in keys if k in wanted)
    return f"{dep['kernel']}_{hashlib.sha1(named.encode()).hexdigest()[:6]}"


def find_package(dep, design, build_root):
    "The dep's package dir and manifest, or an error naming what is missing"
    wanted = dep_design(dep, design)
    require_built(dep["kernel"], wanted, "hls", build_root)
    package_dir = Path(build_root, dep["kernel"],
                       get_design_dir_name(wanted, dep["kernel"]), "package")
    return package_dir, yaml.safe_load(Path(package_dir, "manifest.yaml").read_text())


def blackboxed_deps(kernel_path, impl_spec, tech_type=None):
    "Parse the kernel.yaml file to get the list of blackboxed deps"
    # TODO: support blackboxing on FPGA. Vivado synthesizes the whole design at
    # once, so a packaged dep would need an equivalent of the ASIC flow's ddc.
    if tech_type and is_fpga(tech_type):
        return []

    wanted = KernelConfig.load(kernel_path).blackbox

    # A name the kernel does not instantiate is a stale entry, so it is worth
    # saying rather than stopping. One that names no kernel at all is a typo.
    for name in sorted(set(wanted) - {dep["kernel"] for dep in impl_spec["deps"]}):
        find_kernel(name)
        logging.warning(f"'{impl_spec['name']}' does not use {name}, "
                        f"so it is not blackboxed")

    return [dep for dep in impl_spec["deps"] if dep["kernel"] in wanted]
