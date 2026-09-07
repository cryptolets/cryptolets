import re


def strip_tmpl_prefix(text):
    """"
    Template parameters use a _ prefix, this defines 
    that they are private to the template

    This is a general function which strips the _ prefix
    """
    return re.sub(r"\b_(?=[A-Za-z])", "", text)


def norm_to_py_conv(text):
    """
    Python naming follows lower case convention, while
    C++ naming convention is upper case as the parameters are
    macros in C++.

     e.g. _MRED -> mred, 2*_FIELD::W -> 2*field__w
    """
    text = text.replace("::", "__")
    return strip_tmpl_prefix(text).lower()


def norm_to_cpp_conv(value):
    """
    Python convention to C++
    e.g. mred_mont -> MRED_MONT, a-b -> A::B, True -> 1, 254 -> 254
    """
    if isinstance(value, bool): # before int, a bool is an int
        return int(value)
    if isinstance(value, str):
        return "::".join(p.upper() for p in value.split("-"))
    return value


def walk_tree(node):
    yield node
    for child in node.children:
        yield from walk_tree(child)


def parse_text(node):
    return node.text.decode().strip()


def find_nodes_by_type(src_node, node_type):
    matched_nodes = []
    for node in walk_tree(src_node):
        if node.type == node_type:
            matched_nodes.append(node)
    return matched_nodes