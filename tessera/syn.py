"""
Synthesize a packaged kernel with Design Compiler.

A blackboxed dep was already synthesized on its own, so the parent reads that
result instead of compiling the dep again. This keeps a large design within
what DC can handle, and keeps its runtime close to the parent's own logic.
"""
import re
from pathlib import Path

import yaml

from tessera.blackbox import blackboxed_deps, find_package
from tessera.config import RunConfig
from tessera.templating import render

# Catapult's IO and datapath components, which every packaged design uses
SIFLIBS = ["ccs_in_v1.v", "ccs_out_v1.v", "mgc_io_sync_v2.v"]


def syn_dir(package_dir):
    "Where a package keeps its Design Compiler results"
    return Path(package_dir, "syn")


def child_designs(design, impl_spec, kernel_path, build_root):
    """
    The synthesized deps this design links, as {entity, ddc}.

    A dep is only linked when it was blackboxed, since otherwise its logic is
    already part of this design's own RTL.
    """
    children = []
    for dep in blackboxed_deps(kernel_path, impl_spec, design['tech_type']):
        package_dir, manifest = find_package(dep, design, build_root)
        ddc = syn_dir(package_dir) / f"{dep['kernel']}.ddc"
        if not ddc.exists():
            raise Exception(
                f"No synthesis for '{dep['kernel']}'. Build that kernel with "
                f"syn enabled first.\n  expected: {ddc}")
        children.append({"entity": manifest["entity"], "ddc": str(ddc.resolve())})

    return children


def read_dc_power(design_build_dir, entity):
    """
    The power Design Compiler estimated, in watts.

    This is what the design would use if every net switched as often as the tool
    assumes. A power run measures the real figure instead. The report mixes its
    units, giving dynamic power in mW and leakage in uW.
    """
    report = Path(design_build_dir, "dc_reports", "power.rpt")
    if not report.exists():
        return None

    # The entity also names a row in the wire load table, so match the one
    # whose columns are numbers
    row = re.search(rf"^{re.escape(entity)}\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s",
                    report.read_text(), re.M)
    if not row:
        return None

    switching, internal, leakage = (float(v) for v in row.groups())
    return {
        "switching": switching * 1e-3,
        "internal": internal * 1e-3,
        "leakage": leakage * 1e-6,
        # The reported total rounds the mixed units, so it is summed here instead
        "total": (switching + internal) * 1e-3 + leakage * 1e-6,
    }


def gen_dc_tcl(design, kernel, impl_spec, kernel_path, design_build_dir, max_cores):
    "Write the Design Compiler script for one design"
    conf = RunConfig.load()
    tech = conf.tech[design["tech_type"]]
    catapult_home = Path(conf.tools["catapult"]).expanduser()

    package_dir = design_build_dir / "package"
    manifest = yaml.safe_load(Path(package_dir, "manifest.yaml").read_text())
    build_root = Path(design_build_dir).parent.parent

    report_dir = design_build_dir / "dc_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    syn_dir(package_dir).mkdir(parents=True, exist_ok=True)

    render(
        "dc.tcl.j2",
        design_build_dir / "dc.tcl",
        kernel=kernel,
        entity=manifest["entity"],
        rtl=str(Path(package_dir, manifest["rtl"]).resolve()),
        sdc=str(Path(package_dir, manifest["sdc"]).resolve()),
        target_library=str(Path(tech.lib_db).expanduser()),
        siflibs=[str(catapult_home / "pkgs" / "siflibs" / lib) for lib in SIFLIBS],
        children=child_designs(design, impl_spec, kernel_path, build_root),
        max_cores=max_cores,
        syn_dir=str(syn_dir(package_dir).resolve()),
        report_dir=str(report_dir.resolve()),
    )
    return manifest["entity"]
