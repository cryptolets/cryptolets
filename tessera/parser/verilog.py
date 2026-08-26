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
        parsed_modules.append({
            "name": module_name,
            "ports": module_ports
        })

    return parsed_modules


if __name__ == "__main__":
    from pprint import pprint
    mul_verilog = "/home/gk2657/cryptolets_rehaul/build_v3/l1_mod_mul/bitwidth_254__tech_type_gf12_highperf__period_1.0__ii_1__dep_period_ratio_0.9__curve_bn254__field_base__q_type_fixed_q__redc_type_fixed_rc__mred_mred_mont__mul_type_mul_nor__base_mul_width_254__kar_base_mul_width_254/blackbox/l0_int_mul_9b20f9.v"
    cmul_verilog = "/home/gk2657/cryptolets_rehaul/build_v3/l1_mod_mul/bitwidth_254__tech_type_gf12_highperf__period_1.0__ii_1__dep_period_ratio_0.9__curve_bn254__field_base__q_type_fixed_q__redc_type_fixed_rc__mred_mred_mont__mul_type_mul_nor__base_mul_width_254__kar_base_mul_width_254/blackbox/l0_int_cmul_f4f873.v"
    pprint(parse_verilog(cmul_verilog))
