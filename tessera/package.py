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


def read_design_metrics(metrics_csv, period):
    "The design's own area, latency and delay, from the metrics table"
    row = metrics_csv.read_text().splitlines()[2].split(",")
    return {
        "area": float(row[7]),
        "latency": int(row[2]),
        "delay": round(period - float(row[6]), 4),
    }


def find_rtl(kernel, design, design_build_dir, combinational):
    """
    The RTL to package, and the metrics that describe it.
    For a combinational kernel the RTL is from the CCORE.
    For a sequential kernel the RTL is from the design itself.
    """
    if combinational:
        catapult_dir = design_build_dir / "Catapult"
        solutions = sorted((catapult_dir / "td_ccore_solutions").glob(f"{kernel}_*"))
        if not solutions:
            raise Exception(f"No CCORE solution for '{kernel}' in {catapult_dir}")
        return (solutions[0] / "rtl.v",
                read_ccore_metrics(design_build_dir / "ccore.rpt", kernel))

    return (design_build_dir / "Catapult" / f"{kernel}.v1" / "rtl.v",
            read_design_metrics(design_build_dir / "metrics.csv", design["period"]))


def write_package(kernel, design, design_build_dir, combinational):
    "Write the kernel's RTL and manifest into the design's package dir"
    rtl_path, metrics = find_rtl(kernel, design, design_build_dir, combinational)
    rtl = rtl_path.read_text()

    # The last module is the top, since its children are declared before it
    entity = re.findall(r"^module (\S+)", rtl, re.M)[-1]
    header, body = re.search(rf"^module {entity} \((.*?)\);(.*?)^endmodule",
                             rtl, re.S | re.M).groups()

    package_dir = design_build_dir / "package"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / f"{kernel}.v").write_text(rtl)

    # Catapult writes the constraints beside the RTL, and they name that
    # module's own ports. The wrapper's constraints would match nothing.
    (package_dir / f"{kernel}.sdc").write_text(
        Path(f"{rtl_path}.dc.sdc").read_text())

    manifest = {
        "kernel": kernel,
        "entity": entity,
        "rtl": f"{kernel}.v",
        "sdc": f"{kernel}.sdc",
        "combinational": combinational,
        "ports": parse_module_ports(header, body),
        "params": dict(design),
        **metrics,
    }
    (package_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return package_dir
