"""
Parse the metrics PrimePower reports, per design.
"""
import re
from pathlib import Path

# If the design annotation percent is below this
# this means the design was not simulated correctly
MIN_ANNOTATED = 90.0


def parse_primepower(design):
    """
    Parse the PrimePower's power report
    """
    power_dir = design.build_dir / "power"
    annotation = Path(power_dir, "annotation.rpt")
    annotated = re.search(r"^\s*Nets\s+\d+\(([\d.]+)%\)", annotation.read_text(), re.M)
    if not annotated or float(annotated.group(1)) < MIN_ANNOTATED:
        raise Exception(
            f"Too little of the design was simulated to measure its power.\n  Annotation: {annotation}%"
        )

    report = Path(power_dir, "power.rpt")
    if not report.exists():
        raise Exception(f"PrimePower wrote no report at {report}")

    fields = {
        "switching": r"Net Switching Power\s+=\s+(\S+)",
        "internal": r"Cell Internal Power\s+=\s+(\S+)",
        "leakage": r"Cell Leakage Power\s+=\s+(\S+)",
        "total": r"Total Power\s+=\s+(\S+)",
        "peak": r"Peak Power\s+=\s+(\S+)",
    }

    text = report.read_text()
    power = {}
    for name, pattern in fields.items():
        match = re.search(pattern, text)
        if match:
            power[name] = float(match.group(1))

    if "total" not in power:
        raise Exception(f"No total power in {report}, so the analysis did not finish")

    return power
