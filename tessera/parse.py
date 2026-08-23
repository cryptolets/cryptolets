"""
Read a kernel's template class code with tree-sitter, so the framework
can generate the top from what the kernel author wrote.

A kernel is a class template with a run method. Outputs are the parameters
it takes by reference.
"""
import re
from pathlib import Path

import tree_sitter_cpp
from tree_sitter import Language, Parser


def _tree(header):
    parser = Parser(Language(tree_sitter_cpp.language()))
    return parser.parse(Path(header).read_bytes())


def _text(node):
    return node.text.decode().strip()


def _template_param(node):
    "int _BITWIDTH names its declarator, class _FIELD does not"
    named = node.child_by_field_name("declarator") or node.child_by_field_name("name")
    return _text(named) if named is not None else _text(node).split()[-1]


def _parameter(node):
    declarator = node.child_by_field_name("declarator")
    name = _text(declarator) if declarator is not None else ""
    return {
        "type": _text(node.child_by_field_name("type")),
        "name": name.lstrip("&"),
        "is_output": name.startswith("&"),
    }


def parse_kernel(header):
    """
    The kernel class in this header, as
    {name, template_params, template_decl, params, deps}.

    deps are the member instances, as {kernel, args, name}.
    """
    for node in _walk(_tree(header).root_node):
        if node.type != "template_declaration":
            continue
        cls = next((c for c in node.children if c.type == "class_specifier"), None)
        if cls is None:
            continue

        body = cls.child_by_field_name("body")
        run = next((c for c in body.named_children if _method_name(c) == "run"), None)
        if run is None:
            continue

        tparams = next(c for c in node.children if c.type == "template_parameter_list")
        params = run.child_by_field_name("declarator").child_by_field_name("parameters")

        # Keyed by member name, since sub implementations share their deps
        deps = {d["name"]: d for d in [*_members(body), *_include_members(header)]}

        return {
            "name": _text(cls.child_by_field_name("name")),
            "template_params": [_template_param(p) for p in tparams.named_children],
            "template_decl": [_text(p) for p in tparams.named_children],
            "params": [_parameter(p) for p in params.named_children],
            "deps": list(deps.values()),
        }

    raise Exception(f"No kernel class with a 'run' method in {header}")


def _method_name(node):
    if node.type != "function_definition":
        return None
    declarator = node.child_by_field_name("declarator")
    return _text(declarator.child_by_field_name("declarator"))


def _include_members(header, seen=None):
    "Member instances in headers beside this one, which hold its sub implementations"
    header = Path(header)
    seen = seen if seen is not None else {header}

    for line in header.read_text().splitlines():
        name = re.match(r'#include "(\S+\.h)"', line)
        if not name:
            continue
        inc = header.parent / name[1]
        if not inc.exists() or inc in seen:
            continue
        seen.add(inc)

        for node in _walk(_tree(inc).root_node):
            if node.type == "class_specifier":
                yield from _members(node.child_by_field_name("body"))
        yield from _include_members(inc, seen)


def _members(body):
    "Member instances of other kernels, e.g. l0_int_add_impl<_FIELD::W> int_add_inst"
    deps = []
    for field in body.named_children:
        if field.type != "field_declaration":
            continue
        type_node = field.child_by_field_name("type")
        if type_node is None or type_node.type != "template_type":
            continue
        kernel = _text(type_node.child_by_field_name("name"))
        if not kernel.endswith("_impl"):
            continue
        deps.append({
            "kernel": kernel[:-len("_impl")],
            "args": _text(type_node.child_by_field_name("arguments")).strip("<>").strip(),
            "name": _text(field.child_by_field_name("declarator")),
        })
    return deps


def _walk(node):
    yield node
    for child in node.children:
        yield from _walk(child)


def parse_impl_spec(kernel_name, kernel_path):
    "The kernel class the author wrote, parsed once for every generator"
    header = kernel_path / 'impl' / f"{kernel_name}_impl.h"
    impl_spec = parse_kernel(header)
    if impl_spec['name'] != f"{kernel_name}_impl":
        raise Exception(
            f"{header} defines '{impl_spec['name']}', expected '{kernel_name}_impl'")
    return impl_spec
