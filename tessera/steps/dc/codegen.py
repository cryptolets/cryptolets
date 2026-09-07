"""
Generate the Design Compiler TCL script and
link the child designs that are blackboxed.
"""
import yaml
from pathlib import Path

from tessera.models.config import RunConfig
from tessera.templating import render


def child_designs(design):
    """
    The synthesized children a parent links rather than flattens.
    The RTL calls a child by the name its blackbox was given, so the
    synthesized design is renamed to match before it is linked.
    """
    children = []
    for child_name, designs in design.deps.items():
        for child in designs.values():
            package_dir = child.build_dir / "package"
            ddc = package_dir / "syn" / f"{child_name}.ddc"
            if not ddc.exists():
                raise Exception(f"'{child_name}' is not synthesized for "
                                f"{child.build_dir.name}, so '{design.build_dir.name}' "
                                f"cannot link it")

            manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text())
            children.append({"module": manifest["module"],
                             "renamed": child.blackbox_module,
                             "ddc": str(ddc.resolve())})

    return children


def gen_dc_tcl(design, kernel, max_cores):
    "Write the design's dc.tcl, and return the module it synthesizes"
    tech = RunConfig.load().tech[design.design["tech_type"]]

    package_dir = design.build_dir / "package"
    manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text())

    report_dir = design.build_dir / "reports" / "dc"
    report_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "syn").mkdir(parents=True, exist_ok=True)

    render(
        "dc.tcl.j2",
        design.build_dir / "dc.tcl",
        kernel=kernel.name,
        module=manifest["module"],
        rtl=str((package_dir / manifest["rtl"]).resolve()),
        sdc=str((package_dir / manifest["sdc"]).resolve()),
        target_library=str(Path(tech.lib_db).expanduser()),
        children=child_designs(design) if design.uses_blackboxes else [],
        max_cores=max_cores,
        syn_dir=str((package_dir / "syn").resolve()),
        report_dir=str(report_dir.resolve()),
    )
    return manifest["module"]
