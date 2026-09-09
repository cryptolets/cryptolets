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
            child_info = {"module": manifest["module"],
                          "renamed": child.blackbox_module,
                          "ddc": str(ddc.resolve()),
                          "combinational": manifest["combinational"]}
            if manifest["combinational"]:
                child_info["dont_touch"] = child.blackbox_module
            else:
                wrapper = design.build_dir / "blackbox" / "wrapper" / f"{child.blackbox_module}_wrapper.v"
                child_info["wrapper"] = str(wrapper.resolve())
                child_info["renamed_top"] = f"{child.blackbox_module}_top"
                child_info["dont_touch"] = f"{child.blackbox_module}_top {child.blackbox_module}"
            children.append(child_info)

    return children


def gen_dc_tcl(design, kernel, run_inst):
    """
    Write the design's dc.tcl, and return the module it synthesizes
    """
    tech = RunConfig.load().tech[design.design["tech_type"]]

    package_dir = design.build_dir / "package"
    manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text())
    (package_dir / "syn").mkdir(parents=True, exist_ok=True)

    passes = run_inst.sweep_flags["syn_passes"]
    for n in range(1, passes + 1):
        (design.build_dir / "reports" / "dc" / f"pass_{n}").mkdir(parents=True, exist_ok=True)
        (design.build_dir / "dc" / f"pass_{n}").mkdir(parents=True, exist_ok=True)

    children = child_designs(design) if design.uses_blackboxes else []

    render(
        "dc.tcl.j2",
        design.build_dir / "dc.tcl",
        kernel=kernel.name,
        module=manifest["module"],
        rtl=str((package_dir / manifest["rtl"]).resolve()),
        period=design.design["period"],
        combinational=manifest["combinational"],
        target_library=str(Path(tech.lib_db).expanduser()),
        children=children,
        dont_touch=" ".join(c["dont_touch"] for c in children),
        max_cores=run_inst.threads_per_process,
        passes=passes,
        constraints_tcl=str(Path(run_inst.root_dir, "tessera", "tcl", "dc", "constraints.tcl").resolve()),
        syn_dir=str((package_dir / "syn").resolve()),
        dc_dir=str((design.build_dir / "dc").resolve()),
        report_dir=str((design.build_dir / "reports" / "dc").resolve()),
    )
    return manifest["module"]
