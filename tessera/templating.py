"Shared Jinja environment for all generated files"
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from tessera.const import TEMPLATES_DIR
from tessera.helpers.others import tcl_type
from tessera.parser.common import norm_to_cpp_conv

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
)
env.filters['tcl'] = tcl_type
env.filters['norm_to_cpp_conv'] = norm_to_cpp_conv


def render(template, path, **ctx):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(env.get_template(template).render(**ctx))
