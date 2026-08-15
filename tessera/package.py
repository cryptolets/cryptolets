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


def _bom_row(report, kernel):
    """
    The kernel's row in the report's bill of materials, as {area, delay}.

    The table is fixed width, so the dashed rule under the header gives the
    column spans. Catapult writes no CSV form of this report.
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
            return {"area": float(row["Area Score"]), "delay": float(row["Delay"])}

    raise Exception(f"No bill of materials row for '{kernel}' in {report}")


def _ports(rtl, entity):
    """
    The entity's ports, as {name, dir, width}, read from the RTL itself.

    The module header names them in order. Declarations are matched against
    that list, since functions in the body declare inputs of their own.
    """
    header, body = re.search(rf"^module {entity} \((.*?)\);(.*?)^endmodule",
                             rtl, re.S | re.M).groups()
    names = [n.strip() for n in header.split(",")]

    widths = {}
    for direction, width, declared in re.findall(
            r"^\s*(input|output)\s*(\[[^\]]*\])?\s*([^;]+);", body, re.M):
        for name in (n.strip() for n in declared.split(",")):
            if name in names:
                widths[name] = (direction, _width(width))

    return [{"name": n, "dir": widths[n][0], "width": widths[n][1]} for n in names]


def _width(text):
    "[31:0] is 32 bits, a bare port is 1"
    if not text:
        return 1
    high, low = (int(n) for n in text.strip("[]").split(":"))
    return high - low + 1


def write_package(kernel, design, design_build_dir):
    "Write the kernel's RTL and manifest into the design's package dir"
    catapult_dir = design_build_dir / "Catapult"
    solutions = sorted((catapult_dir / "td_ccore_solutions").glob(f"{kernel}_*"))
    if not solutions:
        raise Exception(f"No CCORE solution for '{kernel}' in {catapult_dir}")

    rtl = (solutions[0] / "rtl.v").read_text()
    # The last module is the top, since its children are declared before it
    entity = re.findall(r"^module (\S+)", rtl, re.M)[-1]

    package_dir = design_build_dir / "package"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / f"{kernel}.v").write_text(rtl)

    manifest = {
        "kernel": kernel,
        "entity": entity,
        "rtl": f"{kernel}.v",
        # A module with no clocked process holds no state, so the parent can
        # wire it combinationally instead of waiting on a latency.
        "combinational": "posedge" not in rtl,
        "ports": _ports(rtl, entity),
        "params": dict(design),
        **_bom_row(design_build_dir / "ccore.rpt", kernel),
    }
    (package_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return package_dir
