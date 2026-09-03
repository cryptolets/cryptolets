"""
Lightweight functions to parse Verilog code with regex.
"""
import re


def find_modules(rtl):
    "Return every module the file defines in the order"
    return re.findall(r"^module (\S+)", rtl, re.M)


def port_width(text):
    "Parse the port widths; e.g. [31:0] is 32 bits, a bare port is 1"
    if not text:
        return 1
    high, low = (int(n) for n in text.strip("[]").split(":"))
    return high - low + 1


def module_ports(rtl, entity):
    "Return the ports of a given module"
    header, body = re.search(rf"^module {entity} \((.*?)\);(.*?)^endmodule",
                             rtl, re.S | re.M).groups()
    names = [n.strip() for n in header.split(",")]

    found = {}
    for direction, width, declared in re.findall(
            r"^\s*(input|output)\s*(\[[^\]]*\])?\s*([^;]+);", body, re.M):
        for name in (n.strip() for n in declared.split(",")):
            if name in names:
                found[name] = {"name": name, "dir": direction,
                               "width": port_width(width)}

    return [found[n] for n in names]


def find_instance(rtl, module):
    "The name a module is instantiated under, and the module holding it"
    m = re.search(rf"^\s+{module}\s+(\w+)\s*\(", rtl, re.M)
    if not m:
        return None

    holders = [(n.group(1), n.start()) for n in re.finditer(r"^module (\S+)", rtl, re.M)
               if n.start() < m.start()]
    return m.group(1), holders[-1][0]
