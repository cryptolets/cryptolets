"""
Generate the Design Compiler TCL script and
link the child designs that are blackboxed.
"""
import yaml
from pathlib import Path

from tessera.deps import blackboxed_deps, dep_design, find_package
from tessera.helper import require_built
from tessera.config import RunConfig
from tessera.templating import render

def child_designs(design, impl_spec, kernel_path, build_root, require=True):
    """
    Link the child designs' .ddc files to the script
    """
    children = []
    for dep in blackboxed_deps(kernel_path, impl_spec, design['tech_type']):
        package_dir, manifest = find_package(dep, design, build_root)
        if require:
            require_built(dep["kernel"], dep_design(dep, design), "syn", build_root)

        ddc = package_dir / "syn" / f"{dep['kernel']}.ddc"
        children.append({"entity": manifest["entity"], "ddc": str(ddc.resolve())})

    return children


def gen_dc_tcl(design, kernel, impl_spec, kernel_path, design_build_dir, max_cores):
    conf = RunConfig.load()
    tech = conf.tech[design["tech_type"]]

    build_root = Path(design_build_dir).parent.parent
    require_built(kernel, design, "hls", build_root)

    package_dir = design_build_dir / "package"
    manifest = yaml.safe_load(Path(package_dir, "manifest.yaml").read_text())

    report_dir = design_build_dir / "reports" / "dc"
    report_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "syn").mkdir(parents=True, exist_ok=True)

    render(
        "dc.tcl.j2",
        design_build_dir / "dc.tcl",
        kernel=kernel,
        entity=manifest["entity"],
        rtl=str(Path(package_dir, manifest["rtl"]).resolve()),
        sdc=str(Path(package_dir, manifest["sdc"]).resolve()),
        target_library=str(Path(tech.lib_db).expanduser()),
        children=child_designs(design, impl_spec, kernel_path, build_root),
        max_cores=max_cores,
        syn_dir=str((package_dir / "syn").resolve()),
        report_dir=str(report_dir.resolve()),
    )
    return manifest["entity"]
