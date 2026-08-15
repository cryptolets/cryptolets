"""
Blackbox a kernel's dependencies with packaged RTL.

A dep is instantiated at its own width, so l0_int_sub<_FIELD::W+1> inside a
32 bit parent needs the 33 bit package. Each dep resolves to a package built
earlier in the sweep, and the generated header points Catapult at its RTL
instead of the implementation.
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from tessera.config import RunConfig
from tessera.helper import get_design_dir_name
from tessera.kernel import find_kernel
from tessera.parse import parse_kernel
from tessera.templating import render


def dep_width(args, design):
    "Evaluate a dep's template argument, e.g. _FIELD::W+1 with W=32 gives 33"
    expr = re.sub(r"\b_FIELD::W\b|\b_BITWIDTH\b", str(design["bitwidth"]), args)
    if not re.fullmatch(r"[\d\s+\-*/()]+", expr):
        raise Exception(f"Cannot evaluate dep width '{args}'")
    return eval(expr)


def dep_design(dep, design):
    """
    The design a dep is packaged as.

    It runs at its own width, and at a fraction of the parent's period so a
    chain of blackboxes still fits the parent's clock. Keeping the ratio
    applies it again to the dep's own deps.
    """
    ratio = design.get("dep_period_ratio", 1)
    return {
        **design,
        "bitwidth": dep_width(dep["args"], design),
        "period": round(design["period"] * ratio, 4),
    }


def find_package(dep, design, build_root):
    "The dep's package dir and manifest, or an error naming what is missing"
    wanted = dep_design(dep, design)
    design_dir = get_design_dir_name(dict(wanted))
    package_dir = Path(build_root, dep["kernel"], design_dir, "package")
    manifest = package_dir / "manifest.yaml"

    if not manifest.exists():
        raise Exception(
            f"No package for '{dep['kernel']}' at bitwidth {wanted['bitwidth']} "
            f"period {wanted['period']}. Build that kernel first.\n"
            f"  expected: {manifest}")

    return package_dir, yaml.safe_load(manifest.read_text())


def gen_blackbox_header(kernel, manifest, rtl, impl_header, include_dir):
    """
    Write the dep's header so it blackboxes the package under synthesis.

    Catapult names the RTL ports after the run parameters, so the parameters
    take the packaged module's port names. A mismatch is not reported, it
    just produces RTL that cannot be elaborated.
    """
    ports = [p for p in manifest["ports"] if p["name"] not in ("clk", "rst")]

    # Verilog ports carry no sign, so it comes from the implementation. The
    # two agree in order, since the RTL ports are built from its parameters.
    for port, param in zip(ports, parse_kernel(impl_header)["params"]):
        port["signed"] = param["type"].rstrip("> ").endswith("true")

    timing = (f'.delay({manifest["delay"]})' if manifest["combinational"] else
              f'.clock_name("clk").latency({manifest["latency"]}).init_delay(1)')

    render(
        "blackbox.h.j2",
        Path(include_dir, f"{kernel}.h"),
        kernel=kernel,
        entity=manifest["entity"],
        rtl=str(Path(rtl).resolve()),
        impl=str(Path(impl_header).resolve()),
        ports=ports,
        outputs=" ".join(p["name"] for p in ports if p["dir"] == "output"),
        area=manifest["area"],
        timing=timing,
    )


def gen_blackbox_headers(design, kernel, kernel_path, design_build_dir):
    "Generate a header and copy the RTL per dep, into a dir that shadows impl"
    kernel_yaml = yaml.safe_load(Path(kernel_path, "kernel.yaml").read_text())

    # The TCL blackboxes whatever this dir holds, so a stale one from an
    # earlier run would keep blackboxing after the flag is turned off.
    include_dir = design_build_dir / "blackbox"
    shutil.rmtree(include_dir, ignore_errors=True)
    if not kernel_yaml.get("blackbox"):
        return

    include_dir.mkdir(parents=True, exist_ok=True)
    build_root = Path(design_build_dir).parent.parent

    for dep in parse_kernel(Path(kernel_path, "impl", f"{kernel}.h"))["deps"]:
        package_dir, manifest = find_package(dep, design, build_root)

        rtl = include_dir / manifest["rtl"]
        rtl.write_text(Path(package_dir, manifest["rtl"]).read_text())

        impl = Path(find_kernel(dep["kernel"]), "impl", f"{dep['kernel']}.h")
        gen_blackbox_header(dep["kernel"], manifest, rtl, impl, include_dir)


def check_rtl_elaborates(design_build_dir, top):
    """
    Elaborate the generated RTL, and raise if a port does not connect.

    Catapult does not check a blackbox declaration against its RTL. A wrong
    port name still reports a clean run and correct metrics, so this is the
    only step that catches it.
    """
    tools = RunConfig.load().tools
    questa = Path(tools["questa"]).expanduser() / "linux_x86_64"
    libs = [Path(tools["dc"]).expanduser() / "dw" / "sim_ver",
            Path(tools["catapult"]).expanduser() / "pkgs" / "siflibs"]

    # Blackboxed deps are instantiated here but defined in their own package
    sources = [design_build_dir / "Catapult" / f"{top}.v1" / "concat_rtl.v",
               *sorted(Path(design_build_dir, "blackbox").glob("*.v"))]

    def run(tool, *args):
        return subprocess.run([str(questa / tool), *args],
                              capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        work = str(Path(tmp, "work"))
        run("vlib", work)
        vlog = ["-work", work]
        for lib in libs:
            vlog += ["-y", str(lib)]
        run("vlog", *vlog, "+libext+.v", *(str(s) for s in sources))
        result = run("vopt", "-work", work, top, "-o", "elab_check")

    errors = [l for l in result.stdout.splitlines() if l.startswith("** Error")]
    if errors:
        raise Exception("Generated RTL does not elaborate:\n  " + "\n  ".join(errors[:5]))
