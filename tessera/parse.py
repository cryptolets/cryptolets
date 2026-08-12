"""
Read a kernel's template function code and extract
the function parameters and return with regex.
"""
import re
from pathlib import Path

COMMENTS = re.compile(r"//.*?$|/\*.*?\*/", re.S | re.M)
# Each parameter ends in "<type> <name>", where the type may hold commas
PARAM = re.compile(r"([\w:]+(?:\s*<[^<>]*>)?)\s+(\w+)\s*(?:,|$)")
# Template parameters look the same but may carry a default, e.g. "bool _MW = false"
TEMPLATE_PARAM = re.compile(r"[\w:]+\s+(\w+)\s*(?:=[^,]*)?(?:,|$)")


def parse_kernel(template_name, header):
    "Return the kernel template as {returns, params, template_params}, in declaration order."
    src = COMMENTS.sub("", Path(header).read_text())

    sig = re.search(
        rf"template\s*<(.*?)>\s*(.+?)\s+{template_name}\s*\((.*?)\)\s*\{{",
        src, re.S,
    )
    if not sig:
        raise Exception(f"No template named '{template_name}' in {header}")

    return {
        "returns": sig.group(2).strip(),
        "params": [{"type": t.strip(), "name": n} for t, n in PARAM.findall(sig.group(3))],
        "template_params": TEMPLATE_PARAM.findall(sig.group(1)),
    }
