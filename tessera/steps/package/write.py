"""
Package a synthesized kernel as reusable RTL along with a manifest
with metrics describing how to blackbox it for Catapult.
"""
import re
import yaml
from pathlib import Path

from tessera.models.common import is_fpga
from tessera.steps.package.verilog import (find_instance, find_modules,
                                           module_ports)

# Where SCVerify puts the design under test, relative to its testbench
SCVERIFY_DUT = "scverify_top/rtl/dut_inst"


# ---- Read metrics for ASICs ----
def read_ccore_metrics(report, kernel):
    """
    Parse the kernel's row in the report's bill of materials, as {area, delay}.
    """
    lines = report.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip().startswith("Component Name"))
    spans = [(m.start(), m.end()) for m in re.finditer(r"-+", lines[start + 1])]
    header = [lines[start][a:b].strip() for a, b in spans]

    for line in lines[start + 2:]:
        if not line.strip():
            break
        row = dict(zip(header, (line[a:b].strip() for a, b in spans)))
        if row["Component Name"].startswith(kernel):
            return {"area": float(row["Area Score"]), "delay": float(row["Delay"]),
                    "latency": 0}

    raise Exception(f"No bill of materials row for '{kernel}' in {report}")


def read_metrics(kernel, design, design_build_dir, combinational):
    "The area, delay and latency the high level run reported"
    reports = design_build_dir / "reports"

    # A CCORE reports its own row, apart from the wrapper's totals
    if combinational:
        return read_ccore_metrics(reports / "ccore.rpt", kernel)

    row = (reports / "metrics.csv").read_text().splitlines()[2].split(",")
    return {
        "area": float(row[7]),
        "latency": int(row[2]),
        "delay": round(design["period"] - float(row[6]), 4),
    }


# ---- Read metrics for FPGAs ----
# FPGA uses resource counts not area in like ASICs
FPGA_METRICS = {
    "luts": "Area(LUTs)",
    "ffs": "Area(FFs)",
    "dsps": "Area(DSP)",
    "brams": "Area(BRAMs)",
    "carry": "Area(CARRY8)",
}

def read_fpga_metrics(metrics_csv):
    """
    Reads the metrics.csv file for FPGA metrics
    """
    lines = metrics_csv.read_text().splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "Vivado"), None)
    if start is None:
        return {}

    header = [col.strip() for col in lines[start + 1].split(",")]
    row = lines[start + 2].split(",")

    found = {}
    for name, column in FPGA_METRICS.items():
        if column in header:
            value = row[header.index(column)].strip()
            found[name] = float(value) if value else 0.0

    return found

def dut_path(rtl, entity):
    """
    Where the wrapper holds the module PrimePower links, as SCVerify sees it.

    Catapult names that instance itself and nests it differently per design,
    so the RTL is walked for it rather than assumed.
    """
    path = []
    while (found := find_instance(rtl, entity)):
        instance, entity = found
        path.append(instance)

    return "/".join([SCVERIFY_DUT, *reversed(path)])


def manifest_ports(rtl, entity, impl_spec):
    """
    Use the verilog funcs to parse the ports definition from the RTL file.
    This will be added to the manifest file.
    """
    # Verilog has no knowledge of sign so we need to parse the impl header file
    signs = {p["name"]: p["type"].rstrip("> ").endswith("true")
             for p in impl_spec["params"]}

    ports = []
    for port in module_ports(rtl, entity):
        name = next((n for n in signs if port["name"].startswith(n)), None)
        ports.append({**port, "signed": bool(name and signs[name])})
    return ports

# ---- Find the RTL and SDC files ----
def find_rtl(kernel, design_build_dir):
    "The whole design in one file, so the package stands alone"
    return design_build_dir / "Catapult" / f"{kernel}.v1" / "concat_rtl.v"


def find_sdc(kernel, design_build_dir, combinational):
    "The constraints naming the packaged module's own ports"
    if not combinational:
        return Path(f"{find_rtl(kernel, design_build_dir)}.dc.sdc")

    # A CCORE sits inside a clocked wrapper, whose constraints name the clock
    catapult_dir = design_build_dir / "Catapult"
    solutions = sorted((catapult_dir / "td_ccore_solutions").glob(f"{kernel}_*"))
    if not solutions:
        raise Exception(f"No CCORE solution for '{kernel}' in {catapult_dir}")
    return solutions[0] / "rtl.v.dc.sdc"


# ---- Top level function to write the package ----
def update_manifest(design_build_dir, **results):
    "Called by Synthesis and Power flows to add their metrics to the package"
    path = Path(design_build_dir, "package", "manifest.yaml")
    manifest = yaml.safe_load(path.read_text())
    manifest.update(results)
    path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return manifest


def write_package(kernel, design, design_build_dir, combinational, impl_spec):
    "Write the kernel's RTL and manifest into the design's package dir"
    # Make the package directory
    package_dir = design_build_dir / "package"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    sdc     = find_sdc(kernel, design_build_dir, combinational)
    metrics = read_metrics(kernel, design, design_build_dir, combinational)
    rtl     = find_rtl(kernel, design_build_dir).read_text()
    (package_dir / f"{kernel}.v").write_text(rtl)

    # FPGA is is handled differently because
    if is_fpga(design["tech_type"]):
        metrics = {**metrics, **read_fpga_metrics(design_build_dir / "reports" / "metrics.csv")}

    # A CCORE is wrapped, so the kernel is named rather than last. Elsewhere
    # the design is the top, whose children are declared before it.
    entity = kernel if combinational else find_modules(rtl)[-1]

    # Store SDC constraints for Synthesis
    if sdc.exists():
        (package_dir / f"{kernel}.sdc").write_text(sdc.read_text())

    manifest = {
        "kernel": kernel,
        "entity": entity,
        "rtl": f"{kernel}.v",
        "sdc": f"{kernel}.sdc" if sdc.exists() else None,
        "combinational": combinational,
        "ports": manifest_ports(rtl, entity, impl_spec),
        "dut_path": dut_path(rtl, entity),
        "params": dict(design),
        **metrics,
    }
    (package_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return package_dir
