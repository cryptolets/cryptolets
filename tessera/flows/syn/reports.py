"What Design Compiler measured, read back from the reports it wrote"
import re
from pathlib import Path


def read_dc_area(design_build_dir):
    "The cell area Design Compiler built, in square micrometres"
    report = Path(design_build_dir, "reports", "dc", "qor.rpt")
    if not report.exists():
        return None

    area = re.search(r"Cell Area:\s+(\S+)", report.read_text())
    return round(float(area.group(1)), 4) if area else None


def read_dc_delay(design_build_dir):
    """
    The critical path Design Compiler achieved, in nanoseconds.

    The high level run estimates this before synthesis, so the two together say
    whether the design still meets its clock once it is built from real cells.
    """
    report = Path(design_build_dir, "reports", "dc", "qor.rpt")
    if not report.exists():
        return None

    period = re.search(r"Critical Path Clk Period:\s+(\S+)", report.read_text())
    slack = re.search(r"Critical Path Slack:\s+(\S+)", report.read_text())
    if not period or not slack or "uninit" in slack.group(1):
        return None

    return round(float(period.group(1)) - float(slack.group(1)), 4)


def read_dc_power(design_build_dir, entity):
    """
    The power Design Compiler estimated, in watts.

    This is what the design would use if every net switched as often as the tool
    assumes. A power run measures the real figure instead. The report mixes its
    units, giving dynamic power in mW and leakage in uW.
    """
    report = Path(design_build_dir, "reports", "dc", "power.rpt")
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
