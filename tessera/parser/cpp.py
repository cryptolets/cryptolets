"""
Parse C++ HLS kernel code with tree-sitter.
"""
from pathlib import Path
import tree_sitter_cpp
from tree_sitter import Language, Parser

from tessera.parser.common import parse_text, find_nodes_by_type


def parse_tmpl_class_name(tmpl_decl):
    cls = find_nodes_by_type(tmpl_decl, "class_specifier")[0]
    return parse_text(cls.child_by_field_name("name"))


def parse_tmpl_params(tmpl_decl):
    params = find_nodes_by_type(tmpl_decl, "template_parameter_list")[0]
    return [parse_text(node) for node in params.named_children]


def parse_func(func_node):
    declarator = func_node.child_by_field_name("declarator")
    params = declarator.child_by_field_name("parameters")

    return (
        parse_text(declarator.child_by_field_name("declarator")),
        [parse_text(node) for node in params.named_children],
    )

def parse_class_field_decl(field_decl):
    tmpl_types = find_nodes_by_type(field_decl, "template_type")
    args = find_nodes_by_type(field_decl, "template_argument_list")

    return {
        "name": parse_text(find_nodes_by_type(field_decl, "field_identifier")[0]),
        "tmpl_name": (
            parse_text(tmpl_types[0].child_by_field_name("name"))
            if tmpl_types else None
        ),
        "tmpl_params": (
            [parse_text(node) for node in args[0].named_children]
            if args else []
        ),
        "declaration": parse_text(field_decl),
    }


def parse_header(header):
    """
    Takes a header file and parses key information.
    Tailored specifically for the impl header of a kernel.
    """
    parser = Parser(Language(tree_sitter_cpp.language()))
    root_node = parser.parse(Path(header).read_bytes()).root_node
    tmpl_decls = find_nodes_by_type(root_node, "template_declaration")

    impl_spec = {}

    for tmpl_decl in tmpl_decls:
        tmpl_name = parse_tmpl_class_name(tmpl_decl)
        tmpl_params = parse_tmpl_params(tmpl_decl)
        func_defs = find_nodes_by_type(tmpl_decl, "function_definition")
        field_decls = find_nodes_by_type(tmpl_decl, "field_declaration")

        impl_spec['tmpl_name'] = tmpl_name
        impl_spec['tmpl_params'] = tmpl_params

        for func_def in func_defs:
            func_name, func_params = parse_func(func_def)
            if func_name == 'run':
                impl_spec['run_params'] = func_params

        impl_spec['field_decls'] = []
        for field_decl in field_decls:
            field_decl_parsed = parse_class_field_decl(field_decl)
            impl_spec['field_decls'].append(field_decl_parsed)

    return impl_spec


if __name__ == "__main__":
    from pprint import pprint

    header = "kernels/l1/l1_mod_mul/impl/l1_mod_mul_impl.h"
    # parser = Parser(Language(tree_sitter_cpp.language()))
    # tree = parser.parse(Path(header).read_bytes())

    # for node in tree.root_node.named_children:
    #     print(node, dir(node))
    impl_spec = parse_header(header)
    pprint(impl_spec)
