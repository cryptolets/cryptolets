"""
Generate Core Catapult Sweep files per-design header files
"""
import re
from pathlib import Path
import yaml

from tessera.field import design_fields, FIELD_CONSTANTS
from tessera.kernel import resolve_deps
from tessera.templating import render
from tessera.parse import parse_kernel

catapult_stages = [
    "new",
    "analyze",
    "compile",
    "libraries",
    "assembly",
    "architect",
    "allocate",
    "schedule",
    "dpfsm",
    "extract",
]

# Catapult stages that save the table to a file
SAVE_TABLE_STAGES = {"schedule", "dpfsm", "extract"}
# Parameters that are not part of the design. curve and field are excluded
# because the generated field descriptor already carries both.
EXCLUDE_PARAMS = ['tech_type', 'curve', 'field']

def gen_params_h(design, enums, design_build_dir):
    enum_defines = {
        value.upper(): i
        for enum, values in enums.items() if enum not in EXCLUDE_PARAMS
        for i, value in enumerate(values)
    }

    params = {}
    for param, value in design.items():
        if param in EXCLUDE_PARAMS:
            continue
        if isinstance(value, bool):
            value = int(value)
        elif isinstance(value, str):
            value = value.upper()
        params[param.upper()] = value

    render(
        "params.h.j2",
        design_build_dir / 'include' / 'params.h',
        enums=enum_defines,
        params=params,
        fields=design_fields(design),
    )

def gen_kernel_src_cpp(design, kernel_name, kernel_path, design_build_dir):
    "Generate the kernel source code from the template implementation"
    impl = parse_kernel(f"{kernel_name}_impl", kernel_path / 'impl' / f"{kernel_name}.h")

    def to_macro(text):
        "A template parameter _X is the params.h macro X"
        text = re.sub(r"\b_FIELD::W\b", "BITWIDTH", text) # to override field's bitwidth
        return re.sub(r"\b_([A-Z][A-Z0-9_]*)\b", r"\1", text)

    # With a fixed modulus the descriptor supplies q, so it is not a port
    fixed = design.get('q_type') == 'fixed_q'

    ports, args = [], []
    for param in impl['params']:
        if fixed and param['name'] in FIELD_CONSTANTS:
            args.append(f"FIELD::{param['name'].upper()}()")
        else:
            ports.append({'type': to_macro(param['type']), 'name': param['name']})
            args.append(param['name'])

    ctx = dict(
        kernel=kernel_name,
        returns=to_macro(impl['returns']),
        ports=ports,
        args=args,
        template_args=", ".join(to_macro(p) for p in impl['template_params']),
    )

    render("kernel_top.h.j2", design_build_dir / 'include' / f'{kernel_name}_top.h', **ctx)
    render("kernel.cpp.j2", design_build_dir / 'src' / f'{kernel_name}.cpp', **ctx)

def gen_catapult_design_tcl(design, design_name, design_build_dir):
    render(
        "design.tcl.j2",
        design_build_dir / "design.tcl",
        design_name=design_name,
        design_build_dir=design_build_dir.resolve(),
        design=design,
    )


def _stage_bodies(kernel_name, kernel_path, root_dir):
    "Kernel-agnostic TCL per stage, before kernel.yaml additions are appended"
    verify_cpp_path = Path(root_dir, 'tessera', 'verify_cpp')
    verify_cpp_src_path = verify_cpp_path / 'src'
    dep_paths = resolve_deps(kernel_path, Path(root_dir, 'kernels'))

    include_paths = [
        verify_cpp_path / 'include',
        Path(kernel_path, 'impl'),
        *(p / 'impl' for p in dep_paths),
    ]
    include_paths_str = "\n".join(f"  {p.resolve()}" for p in include_paths)

    analyze_stage = [
        "options set Input/SearchPath {\n" + include_paths_str + "\n} -append",
        "options set Input/SearchPath [file join $design_build_dir include] -append",
        "solution file add [file join $design_build_dir src " + f"{kernel_name}.cpp]",
        f"solution file add [file join {(Path(kernel_path) / f'{kernel_name}_tb.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(verify_cpp_src_path / 'csvparser.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(verify_cpp_src_path / 'tb_helper.cpp').resolve()}] -exclude true",
    ]

    compile_stage = [
        f"solution design set {kernel_name} -top",
        "directive set -DESIGN_GOAL latency",
        "directive set -OUTPUT_REGISTERS false",
        "directive set -OPT_CONST_MULTS full",
    ]

    libraries_stage = [
        "run_osci_test $test_cpp $test_cpp_only $design_build_dir",
        "set_tech_lib $tech_type $root_dir",
        "set_clock $period",
    ]

    return {'analyze': analyze_stage, 'compile': compile_stage, 'libraries': libraries_stage}


def gen_catapult_kernel_tcl(sweep_conf, kernel_name, kernel_path, kernel_build_dir, root_dir):
    kernel_yaml = yaml.safe_load(Path(kernel_path, 'kernel.yaml').read_text())

    bodies = _stage_bodies(kernel_name, kernel_path, root_dir)
    for stage, body in kernel_yaml.get('stages', {}).items():
        bodies.setdefault(stage, []).extend(body.splitlines())

    stages = [
        {
            'name': stage,
            'body': "\n".join(bodies.get(stage, [])),
            'save_table': stage in SAVE_TABLE_STAGES,
        }
        for stage in catapult_stages
    ]

    render(
        "kernel.tcl.j2",
        kernel_build_dir / "kernel.tcl",
        root_dir=root_dir,
        kernel_name=kernel_name,
        catapult_util_tcl=Path(root_dir, 'tessera', 'tcl', 'catapult', 'util.tcl').resolve(),
        catapult_init_tcl=Path(root_dir, 'tessera', 'tcl', 'catapult', 'init.tcl').resolve(),
        catapult_verify_tcl=Path(root_dir, 'tessera', 'tcl', 'catapult', 'verify.tcl').resolve(),
        flags=sweep_conf['flags'],
        stages=stages,
    )
