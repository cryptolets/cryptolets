"""
Parse Verilog code with tree-sitter.
"""
from pathlib import Path
import tree_sitter_verilog
from tree_sitter import Language, Parser
from simpleeval import simple_eval

from tessera.parser.common import parse_text, find_nodes_by_type


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
        val = parse_text(find_nodes_by_type(param_decl_node, "constant_expression")[0])
        if not val.isdigit(): continue
        variables[var] = val

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
            width = parse_text(widths[i])
            for var, val in variables.items():
                width = width.replace(var, val)
            widths[i] = simple_eval(str(width))

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
