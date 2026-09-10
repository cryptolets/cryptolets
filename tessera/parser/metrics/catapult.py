"""
Parse the metrics Catapult reports, per design.
"""
import re


def parse_catapult_csv(path, section):
    """
    One section of Catapult's metrics.csv as {column: value}, from its first
    data row, which is the design's total. The file holds several sections,
    each a blank line apart, named by its first line.
    """
    for block in path.read_text().split("\n\n"):
        lines = block.strip().splitlines()
        if lines and lines[0].strip() == section:
            header = [col.strip() for col in lines[1].split(",")]
            row = [cell.strip() for cell in lines[2].split(",")]
            return dict(zip(header, row))
    raise Exception(f"No '{section}' section in {path}")


def parse_catapult(design):
    "The area, latency and delay of a sequential design"
    reports = design.build_dir / "reports"
    general = parse_catapult_csv(reports / "metrics.csv", "General")
    timing = parse_catapult_csv(reports / "metrics.csv", "Timing")
    return {
        "area": float(general["Area"]),
        "latency": int(general["Latency Cycle"]),
        "delay": round(float(timing["Clock Period"]) - float(timing["Slack"]), 4),
    }


def parse_catapult_ccore(design, kernel):
    """
    The area and delay of a combinational design, which is a CCORE.
    The metrics table reports the wrapper's totals, so the CCORE's own row
    is read from the bill of materials instead.
    """
    report = design.build_dir / "reports" / "ccore.rpt"
    lines = report.read_text().splitlines()

    # Columns are fixed width, laid out by the dashes under the header
    start = next(i for i, line in enumerate(lines)
                 if line.strip().startswith("Component Name"))
    spans = [(m.start(), m.end()) for m in re.finditer(r"-+", lines[start + 1])]
    header = [lines[start][a:b].strip() for a, b in spans]

    for line in lines[start + 2:]:
        if not line.strip():
            break
        row = dict(zip(header, (line[a:b].strip() for a, b in spans)))
        if row["Component Name"].startswith(kernel.name):
            return {
                "area": float(row["Area Score"]),
                "latency": 0,
                "delay": float(row["Delay"]),
            }

    raise Exception(f"No bill of materials row for '{kernel.name}' in {report}")


# FPGA reports resource counts rather than an area
FPGA_METRICS = {
    "luts": "Area(LUTs)",
    "ffs": "Area(FFs)",
    "dsps": "Area(DSP)",
    "brams": "Area(BRAMs)",
    "carry": "Area(CARRY8)",
}


def parse_catapult_fpga(design):
    "The resources Vivado used, from the section it adds to metrics.csv"
    metrics_path = design.build_dir / "reports" / "metrics.csv"
    if "Vivado" not in metrics_path.read_text().splitlines():
        return {}
    vivado = parse_catapult_csv(metrics_path, "Vivado")
    return {name: float(vivado[column] or 0)
            for name, column in FPGA_METRICS.items() if column in vivado}