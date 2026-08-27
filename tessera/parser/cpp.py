"""
Parse C++ HLS kernel code with tree-sitter.
"""
from pathlib import Path
import tree_sitter_cpp
from tree_sitter import Language, Parser

from tessera.parser.common import parse_text, find_nodes_by_type
from tessera.const import KERNELS_DIR


SPECIAL_CASE_INCLUDES = {"l0_int_mul_kar.h", "l0_int_mul_sb.h"}


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
    decl_type = field_decl.child_by_field_name("type").type
    name = parse_text(find_nodes_by_type(field_decl, "field_identifier")[0])
    declaration = parse_text(field_decl)
    
    # Is a dependency field declaration
    if decl_type == "template_type":
        tmpl_types = find_nodes_by_type(field_decl, "template_type")
        args = find_nodes_by_type(field_decl, "template_argument_list")

        return {
            "name": name,
            "decl_type": decl_type,
            "tmpl_name": parse_text(tmpl_types[0].child_by_field_name("name")),
            "tmpl_params": [parse_text(node) for node in args[0].named_children],
            "declaration": declaration,
        }

    else:
        return {
            "name": name,
            "decl_type": decl_type,
            "tmpl_name": None,
            "tmpl_params": [],
            "declaration": declaration,
        }

def parse_include(root_node):
    include_nodes = find_nodes_by_type(root_node, "preproc_include")
    include_paths = []

    for include_node in include_nodes:
        include_path_node = find_nodes_by_type(include_node, "string_content")
        if include_path_node:
            include_paths.append(parse_text(include_path_node[0]))
    return include_paths


def parse_header(header):
    """
    Takes a header file and parses key information.
    Tailored specifically for the impl header of a kernel.
    """
    parser = Parser(Language(tree_sitter_cpp.language()))
    root_node = parser.parse(Path(header).read_bytes()).root_node
    tmpl_decls = find_nodes_by_type(root_node, "template_declaration")
    impl_spec = {
        "include_paths": parse_include(root_node),
    }

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


def get_path_to_include(include_path):
    """
    We look for which include is in a kernel impl dir, 
    but not a kernel impl itself
    """
    for kernel in Path(KERNELS_DIR).glob("*/*"):
        header = kernel / "impl" / include_path
        if header.exists():
            return header
    return None


def parse_kernel_impl(kernel_impl, memo={}):
    """
    Parse kernel and its non-kernel dependencies recursively
    """
    if kernel_impl not in memo:
        impl_spec = parse_header(kernel_impl)
        impl_spec['deps'] = {}

        # Resolve recursive dependencies which are not kernel impls
        for include_path in impl_spec['include_paths']:
            if include_path.endswith("impl.h"):
                continue
            if include_path in SPECIAL_CASE_INCLUDES:
                continue

            full_include_path = get_path_to_include(include_path)
            if full_include_path:
                impl_spec['deps'][include_path] = parse_kernel_impl(full_include_path, memo)

        memo[kernel_impl] = impl_spec
    return memo[kernel_impl]
        

if __name__ == "__main__":
    from pprint import pprint

    header = "kernels/l0/l0_int_mul/impl/l0_int_mul_impl.h"
    # header = "kernels/l1/l1_mod_mul/impl/l1_mod_mul_impl.h"
    # header = "kernels/l1/l1_mod_cmul/impl/l1_mod_cmul_impl.h"
    # parser = Parser(Language(tree_sitter_cpp.language()))
    # tree = parser.parse(Path(header).read_bytes())

    # for node in tree.root_node.named_children:
    #     print(node, dir(node))
    impl_spec = parse_kernel_impl(header)
    pprint(impl_spec)
