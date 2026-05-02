import yaml

class FlowList(list):
    "List rendered inline: [1, 2, 3]"

class LiteralStr(str):
    "String rendered as | block (preserves newlines)"

def _flow_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

def _literal_str(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(FlowList, _flow_list)
yaml.add_representer(LiteralStr, _literal_str)