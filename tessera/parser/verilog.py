"""
Parse Verilog code with tree-sitter.
"""
import re
from pathlib import Path
import tree_sitter_verilog
from tree_sitter import Language, Parser
from simpleeval import simple_eval

from tessera.parser.common import parse_text, find_nodes_by_type


def normalize_verilog_ints(expr):
    """
    Replace Verilog int literals in an expression with decimal ints.

    Examples:
      "32'd4"            -> "4"
      "8'hff + 1"        -> "255 + 1"
      "width_a-1"        -> "width_a-1"   (unchanged)
      "4'b10xz"          -> "4'b10xz"     (unchanged, contains x/z)
      "16'h0f_0f + var"  -> "3855 + var"
    """
    def to_dec(match):
        base = {"d": 10, "h": 16, "o": 8, "b": 2}[match.group(1).lower()]
        digits = match.group(2).lower().replace("_", "")
        if "x" in digits or "z" in digits:
            return match.group(0)
        return str(int(digits, base))

    # Match Verilog based literals like 32'd4, 'hff, 8'b1010, 6'o77 (case-insensitive),
    # capture base and digits, then replace each match with its decimal value via to_dec.
    return re.compile(r"(?i)\b(?:\d+)?'([dhob])([0-9a-f_xz]+)\b").sub(to_dec, expr)


def eval_expr(expr, variables):
    "Evaluate simple width/parameter expressions, including 32'd4 style literals."
    return simple_eval(normalize_verilog_ints(expr), names=variables)


def parse_module_name(module_decl_node):
    return parse_text(
        find_nodes_by_type(module_decl_node, "simple_identifier")[0]
    )


def parse_module_ports(module_decl_node):
    "Parses port declarations, and resolves variables defining widths"
    ports = []
    port_decl_nodes = find_nodes_by_type(module_decl_node, "port_declaration")
    param_decl_nodes = find_nodes_by_type(module_decl_node, "parameter_declaration")
    variables = {}

    for param_decl_node in param_decl_nodes:
        var = parse_text(find_nodes_by_type(param_decl_node, "simple_identifier")[0])
        expr = parse_text(find_nodes_by_type(param_decl_node, "constant_expression")[0])
        variables[var] = eval_expr(expr, variables)

    for port_node in port_decl_nodes:
        name = parse_text(find_nodes_by_type(port_node, "port_identifier")[0])
        in_decls = find_nodes_by_type(port_node, "input_declaration")
        out_decls = find_nodes_by_type(port_node, "output_declaration")

        if in_decls:
            direction = "input"
        elif out_decls:
            direction = "output"
        else:
            continue

        widths = find_nodes_by_type(port_node, "constant_expression")
        for i in range(len(widths)):
            widths[i] = eval_expr(parse_text(widths[i]), variables)

        width = max(widths) - min(widths) + 1 if widths else 1

        ports.append({
            "name": name,
            "direction": direction,
            "width": width
        })

    return ports


def parse_verilog(verilog):
    "Parse module names and ports from a Verilog file"
    parser = Parser(Language(tree_sitter_verilog.language()))
    root_node = parser.parse(Path(verilog).read_bytes()).root_node

    module_decl_nodes = find_nodes_by_type(root_node, "module_declaration")
    parsed_modules = []

    for module_decl_node in module_decl_nodes:
        module_name = parse_module_name(module_decl_node)
        module_ports = parse_module_ports(module_decl_node)

        # parse what modules are instantiated and their names
        instances = [
            {"module": parse_text(find_nodes_by_type(n, "simple_identifier")[0]),
             "inst": parse_text(find_nodes_by_type(n, "instance_identifier")[0])}
            for n in find_nodes_by_type(module_decl_node, "module_instantiation")
        ]

        parsed_modules.append({
            "name": module_name,
            "ports": module_ports,
            "instances": instances,
        })

    return parsed_modules


if __name__ == "__main__":
    from pprint import pprint
    cmul_verilog = ("build_v3/l0_int_cmul/bitwidth_254__tech_type_gf12_highperf__period_0.9__ii_1"
                    "__curve_bn254__field_base__cmul_const_cmul_q__mred_mred_mont/package/l0_int_cmul.v")
    pprint(parse_verilog(cmul_verilog))
