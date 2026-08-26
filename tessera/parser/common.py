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