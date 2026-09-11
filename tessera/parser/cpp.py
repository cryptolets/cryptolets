"""
Read a kernel's C++ two ways.

The header, with tree-sitter: the impl class, its template parameters and
the signature of run. This is per kernel, and is what the generated top
needs.

The instantiation, with gcc: which children a design of the kernel uses. A
kernel's impl declares a member for every child it could use, and picks
between them with `if constexpr` on the design's parameters, so only the
compiler knows which survive. The design's top is compiled with debug info,
and the DWARF is read: every `<kernel>_impl<...>` class whose `run` was
emitted is a child the design uses, and the class carries its template
parameters by name and value. This is per design.
"""
import subprocess
from pathlib import Path

import tree_sitter_cpp
from elftools.elf.elffile import ELFFile
from tree_sitter import Language, Parser

from tessera.const import KERNELS_DIR, ROOT_DIR
from tessera.models.config import RunConfig
from tessera.models.sweep import Sweep
from tessera.parser.common import parse_text, find_nodes_by_type, norm_to_py_conv
from tessera.steps.gen.codegen import gen_kernel_top, gen_params_h

# What gcc compiled, kept in the design's build dir so a wrong answer can be traced
GCC_DIR = "gcc"


# --- the header, with tree-sitter ---

def func_name(func):
    return parse_text(func.child_by_field_name("declarator").child_by_field_name("declarator"))


def parse_run_params(func):
    params = func.child_by_field_name("declarator").child_by_field_name("parameters")
    return [{
        "name": parse_text(node.child_by_field_name("declarator")).lstrip("&"),
        "text": parse_text(node),
    } for node in params.named_children]


def parse_tmpl_params(tmpl_decl):
    "Parse the template parameter list, in the order it is written"
    parsed_params = []
    all_params = find_nodes_by_type(tmpl_decl, "template_parameter_list")[0]

    for param_decl in all_params.named_children:
        # Params where the type is not a class/struct
        if param_decl.type in ("parameter_declaration", "optional_parameter_declaration"):
            name = norm_to_py_conv(parse_text(param_decl.child_by_field_name("declarator")))
            default_value = param_decl.child_by_field_name("default_value")
            default = norm_to_py_conv(parse_text(default_value)) if default_value else None
            parsed_params.append({
                "name": name,
                "type": parse_text(param_decl.child_by_field_name("type")),
                "default": default if default != name else None
            })

        # Params where the type is a class/struct
        elif param_decl.type == "type_parameter_declaration":
            parsed_params.append({
                "name": norm_to_py_conv(
                    parse_text(find_nodes_by_type(param_decl, "type_identifier")[0])),
                "type": "class",
                "default": None
            })

        elif param_decl.type == "optional_type_parameter_declaration":
            parsed_params.append({
                "name": norm_to_py_conv(
                    parse_text(param_decl.child_by_field_name("name"))),
                "type": "class",
                "default": norm_to_py_conv(
                    parse_text(param_decl.child_by_field_name("default_type"))
                )
            })

    return parsed_params


def parse_header(header):
    parser = Parser(Language(tree_sitter_cpp.language()))
    root = parser.parse(Path(header).read_bytes()).root_node

    # The impl class; a consts struct beside it carries derived constants
    tmpl_decls = [d for d in find_nodes_by_type(root, "template_declaration")
                  if find_nodes_by_type(d, "class_specifier")]
    assert len(tmpl_decls) == 1, f"{header}: one template class per header"
    tmpl_decl = tmpl_decls[0]

    run = next(f for f in find_nodes_by_type(tmpl_decl, "function_definition")
               if func_name(f) == "run")

    return {
        "tmpl_name": parse_text(find_nodes_by_type(tmpl_decl, "class_specifier")[0]
                                .child_by_field_name("name")),
        "tmpl_params": parse_tmpl_params(tmpl_decl),
        "run_params": parse_run_params(run),
    }


# --- the instantiation, with gcc ---

def die_name(die):
    attr = die.attributes.get("DW_AT_name")
    return attr.value.decode() if attr else ""


def struct_ref(die):
    "A nested struct by its path: ARB_FIELD_32::Q_PRIME -> arb_field_32-q_prime"
    parts = []
    while die.tag in ("DW_TAG_class_type", "DW_TAG_structure_type"):
        parts.append(die_name(die).lower())
        die = die.get_parent()
    return "-".join(reversed(parts))


def template_params(children, ref):
    "The template arguments of a class, as design parameters"
    params = {}
    for die in children:
        name = norm_to_py_conv(die_name(die))
        if die.tag == "DW_TAG_template_value_param":
            # An int that holds one of the sweep's enums is named again,
            # so `_MRED = 0` reads as mred_mont
            value = die.attributes["DW_AT_const_value"].value
            enums = Sweep.enums().get(name)
            params[name] = enums[value] if enums else value
        elif die.tag == "DW_TAG_template_type_param":
            params[name] = struct_ref(ref(die, "DW_AT_type"))
    return params


def live_classes(obj):
    "(kernel name, {param: value}) for every impl class whose run was emitted"
    with obj.open("rb") as f:
        dwarf = ELFFile(f).get_dwarf_info()
        for cu in dwarf.iter_CUs():
            dies = {die.offset: die for die in cu.iter_DIEs()}

            def ref(die, attr):
                "The DIE an attribute points at"
                return dies[die.attributes[attr].value + cu.cu_offset]

            # A method declared in a class only gets a body if the compiler
            # used it. The body is its own DIE, pointing back at the
            # declaration, so the declarations with a body are the live ones.
            defined = {ref(die, "DW_AT_specification").offset for die in dies.values()
                       if die.tag == "DW_TAG_subprogram"
                       and "DW_AT_specification" in die.attributes
                       and "DW_AT_low_pc" in die.attributes}

            for die in dies.values():
                if die.tag not in ("DW_TAG_class_type", "DW_TAG_structure_type"):
                    continue
                name = die_name(die).split("<")[0]
                if not name.endswith("_impl"):
                    continue

                children = list(die.iter_children())
                runs = [c for c in children
                        if c.tag == "DW_TAG_subprogram" and die_name(c) == "run"]
                if any(run.offset in defined for run in runs):
                    yield name.removesuffix("_impl"), template_params(children, ref)


def compile_with_debug_info(gcc_dir, source):
    catapult = Path(RunConfig.load().tools["catapult"]).expanduser()
    include_dirs = [
        gcc_dir / "include",
        ROOT_DIR / "tessera" / "cpp" / "include",
        *sorted(p.resolve() for p in KERNELS_DIR.glob("*/*/impl")),
        catapult / "shared" / "include",
    ]

    obj = source.with_suffix(".o")
    cmd = ["g++", "-std=c++17", "-g", "-O0", "-c", "-o", str(obj),
           *[f"-I{d}" for d in include_dirs], str(source)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise Exception(f"{source} does not compile:\n{result.stderr}")
    return obj


def live_instances(design, kernel):
    """
    The children a design of this kernel instantiates, as
    child kernel name -> list of {param: value}, one per distinct run.
    """
    gcc_dir = design.build_dir / GCC_DIR
    gen_params_h(design, out_dir=gcc_dir)
    gen_kernel_top(design, kernel, out_dir=gcc_dir)

    # Taking run's address makes gcc emit it, and so everything it calls
    source = gcc_dir / "src" / f"{kernel.name}_top.cpp"
    source.write_text(source.read_text() + f"static auto use_run = &{kernel.name}_top::run;\n")
    obj = compile_with_debug_info(gcc_dir, source)

    instances = {}
    for name, params in live_classes(obj):
        if name != kernel.name and params not in instances.setdefault(name, []):
            instances[name].append(params)
    return instances
