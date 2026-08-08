"Shared Jinja environment for all generated files"
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from framework.helper import tcl_type

TEMPLATES_DIR = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
)
env.filters['tcl'] = tcl_type


def render(template, path, **ctx):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(env.get_template(template).render(**ctx))
