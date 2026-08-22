"""
Package a synthesized kernel as reusable RTL.

The kernel is built as a combinational CCORE inside a wrapper, so Catapult
writes the kernel's own RTL to td_ccore_solutions and the wrapper carries the
clock and the testbench. The package holds that CCORE RTL and a manifest
describing how to blackbox it.
"""
import re
from pathlib import Path

import yaml

from tessera.config import is_fpga


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


def parse_module_ports(header, body):
    "Parse the module's ports, as {name, dir, width}, in declaration order."
    names = [n.strip() for n in header.split(",")]
    found = {}

    for direction, width, declared in re.findall(
            r"^\s*(input|output)\s*(\[[^\]]*\])?\s*([^;]+);", body, re.M):
        for name in (n.strip() for n in declared.split(",")):
            if name in names:
                found[name] = {"name": name, "dir": direction, "width": port_width(width)}

    return [found[n] for n in names]


def port_width(text):
    "[31:0] is 32 bits, a bare port is 1"
    if not text: return 1
    high, low = (int(n) for n in text.strip("[]").split(":"))
    return high - low + 1


def manifest_ports(header, body, impl_spec):
    """
    The module's ports, each carrying the sign its parameter was declared with.

    Verilog holds no sign, and Catapult renames a port to carry its handshake,
    so the name a parameter took is the prefix of the ones built from it.
    """
    signs = port_signs(impl_spec)

    ports = []
    for port in parse_module_ports(header, body):
        name = next((n for n in signs if port["name"].startswith(n)), None)
        ports.append({**port, "signed": bool(name and signs[name])})
    return ports


def read_design_metrics(metrics_csv, period):
    "The design's own area, latency and delay, from the metrics table"
    row = metrics_csv.read_text().splitlines()[2].split(",")
    return {
        "area": float(row[7]),
        "latency": int(row[2]),
        "delay": round(period - float(row[6]), 4),
    }


# What an FPGA design is measured in, since it holds parts rather than cells
FPGA_METRICS = {
    "luts": "Area(LUTs)",
    "ffs": "Area(FFs)",
    "dsps": "Area(DSP)",
    "brams": "Area(BRAMs)",
    "carry": "Area(CARRY8)",
}


def read_fpga_metrics(metrics_csv):
    """
    What Vivado reported, as {luts, ffs, dsps, brams, carry}.

    The table holds a section per tool, and Catapult writes Vivado's once it
    has run. The first row of that section is the design's own total.
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


def find_rtl(kernel, design, design_build_dir, combinational):
    """
    The RTL to package, the constraints for it, and the metrics describing it.

    concat_rtl.v is the whole design in one file, defining the datapath and IO
    components the kernel only instantiates, so the package stands alone.
    """
    rtl = design_build_dir / "Catapult" / f"{kernel}.v1" / "concat_rtl.v"

    if combinational:
        # The kernel here is a CCORE inside a clocked wrapper, and only the
        # CCORE's own constraints name its ports. The wrapper's name the clock.
        catapult_dir = design_build_dir / "Catapult"
        solutions = sorted((catapult_dir / "td_ccore_solutions").glob(f"{kernel}_*"))
        if not solutions:
            raise Exception(f"No CCORE solution for '{kernel}' in {catapult_dir}")
        return (rtl, solutions[0] / "rtl.v.dc.sdc",
                read_ccore_metrics(design_build_dir / "ccore.rpt", kernel))

    return (rtl, Path(f"{rtl}.dc.sdc"),
            read_design_metrics(design_build_dir / "metrics.csv", design["period"]))


def update_manifest(design_build_dir, **results):
    """
    Add a later stage's results to the package.

    Catapult writes the manifest when it packages the RTL, and synthesis and
    power add what they measured, so one file describes the finished design.
    """
    path = Path(design_build_dir, "package", "manifest.yaml")
    manifest = yaml.safe_load(path.read_text())
    manifest.update(results)
    path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return manifest


def port_signs(impl_spec):
    "Whether each of the run parameters is signed, keyed by its name"
    return {p["name"]: p["type"].rstrip("> ").endswith("true")
            for p in impl_spec["params"]}


def write_package(kernel, design, design_build_dir, combinational, impl_spec):
    "Write the kernel's RTL and manifest into the design's package dir"
    rtl_path, sdc, metrics = find_rtl(kernel, design, design_build_dir, combinational)
    rtl = rtl_path.read_text()

    # An FPGA holds parts rather than cells, so Vivado's counts describe it
    # better than the area the high level run estimated
    if is_fpga(design["tech_type"]):
        metrics = {**metrics, **read_fpga_metrics(design_build_dir / "metrics.csv")}

    # A CCORE is wrapped, so the kernel is named rather than last. Elsewhere
    # the design is the top, whose children are declared before it.
    entity = kernel if combinational else re.findall(r"^module (\S+)", rtl, re.M)[-1]
    header, body = re.search(rf"^module {entity} \((.*?)\);(.*?)^endmodule",
                             rtl, re.S | re.M).groups()

    package_dir = design_build_dir / "package"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / f"{kernel}.v").write_text(rtl)

    # Only the ASIC flow writes constraints, since they are for Design Compiler
    if sdc.exists():
        (package_dir / f"{kernel}.sdc").write_text(sdc.read_text())

    manifest = {
        "kernel": kernel,
        "entity": entity,
        "rtl": f"{kernel}.v",
        "sdc": f"{kernel}.sdc" if sdc.exists() else None,
        "combinational": combinational,
        "ports": manifest_ports(header, body, impl_spec),
        "params": dict(design),
        **metrics,
    }
    (package_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return package_dir
