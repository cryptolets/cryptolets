"""
Generate Core Catapult Sweep files per-design header files
"""
import re
from pathlib import Path
import yaml

from tessera.config import RunConfig, Sweep
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

# Parameters that are not part of the design. 
# Curve and field are excluded because the generated field
# descriptor already carries both.
EXCLUDE_PARAMS = ['tech_type', 'curve', 'field', 'dep_period_ratio']

def gen_params_h(design, design_build_dir):
    enum_defines = {
        value.upper(): i
        for enum, values in Sweep.enums().items() if enum not in EXCLUDE_PARAMS
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

def to_macro(text):
    "A template parameter _X is the params.h macro X"
    text = re.sub(r"\b_FIELD::W\b", "BITWIDTH", text) # to override field's bitwidth
    return re.sub(r"\b_([A-Z][A-Z0-9_]*)\b", r"\1", text)


def _top_ports(impl, design):
    "The top's ports and the arguments it forwards to the impl"
    # With a fixed modulus the descriptor supplies q, so it is not a port
    fixed = design.get('q_type') == 'fixed_q'

    ports, args = [], []
    for param in impl['params']:
        if fixed and param['name'] in FIELD_CONSTANTS:
            args.append(f"FIELD::{param['name'].upper()}()")
        else:
            ports.append({
                'type': to_macro(param['type']),
                'name': param['name'],
                'ref': param['is_output'],
            })
            args.append(param['name'])
    return ports, args


def read_impl_spec(kernel_name, kernel_path):
    "The kernel class the author wrote, parsed once for every generator"
    header = kernel_path / 'impl' / f"{kernel_name}_impl.h"
    impl_spec = parse_kernel(header)
    if impl_spec['name'] != f"{kernel_name}_impl":
        raise Exception(
            f"{header} defines '{impl_spec['name']}', expected '{kernel_name}_impl'")
    return impl_spec


def gen_kernel_top(
    design, kernel_name, impl_spec, design_build_dir,
    combinational=False # default is sequential
):
    """
    Generate the top header and the source file Catapult synthesizes.
    A combinational kernel is a CCORE inside a wrapper.
    A sequential kernel is the top itself.
    """
    ports, args = _top_ports(impl_spec, design)
    ctx = dict(
        kernel=kernel_name,
        ports=ports,
        args=args,
        combinational=combinational,
        template_args=", ".join(to_macro(p) for p in impl_spec['template_params']),
    )

    render("kernel_top.h.j2", design_build_dir / 'include' / f'{kernel_name}_top.h', **ctx)
    render("kernel.cpp.j2", design_build_dir / 'src' / f'{kernel_name}_top.cpp', **ctx)

def gen_catapult_design_tcl(design, kernel_name, design_name, design_build_dir,
                            comb_chk=False, combinational=False):
    # Catapult supplies some libraries itself, so lib_file can be empty
    tech = RunConfig.load().tech[design['tech_type']].model_dump()
    tech = {k: str(Path(v).expanduser()) if v and k.endswith(('_path', '_file')) else (v or "")
            for k, v in tech.items()}

    render(
        "design.tcl.j2",
        design_build_dir / "design.tcl",
        design_name=design_name,
        design_build_dir=design_build_dir.resolve(),
        design=design,
        tech=tech,
        comb_chk=comb_chk,
        # A combinational kernel is a CCORE inside a top of its own
        top_class=f"{kernel_name}_top" if combinational else kernel_name,
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
        # The blackbox dir comes first, so a generated header shadows the
        # kernel's own when that dep is blackboxed.
        "options set Input/SearchPath [file join $design_build_dir blackbox] -append",
        "options set Input/SearchPath {\n" + include_paths_str + "\n} -append",
        "options set Input/SearchPath [file join $design_build_dir include] -append",
        "solution file add [file join $design_build_dir src " + f"{kernel_name}_top.cpp]",
        "add_blackbox_rtl $design_build_dir",
        f"solution file add [file join {(Path(kernel_path) / f'{kernel_name}_tb.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(verify_cpp_src_path / 'csvparser.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(verify_cpp_src_path / 'tb_helper.cpp').resolve()}] -exclude true",
    ]

    compile_stage = [
        # A combinational kernel wraps its CCORE, so the top class differs
        "solution design set $top_class.run -top",
        "directive set -CCORE_POINTS 1",
        "directive set -DESIGN_GOAL latency",
        "directive set -OUTPUT_REGISTERS false",
    ]

    libraries_stage = [
        "run_osci_test $test_cpp $test_cpp_only $design_build_dir",
        "set_tech_lib $tech_type $root_dir $tech_lib_path $tech_catapult_lib_name \
     $tech_vendor $tech_technology $tech_catapult_lib_file \
     $tech_family $tech_speed $tech_part",
        "set_clock $period",
    ]

    return {'analyze': analyze_stage, 'compile': compile_stage, 'libraries': libraries_stage}


def gen_catapult_kernel_tcl(sweep_flags, kernel_name, kernel_path, kernel_build_dir,
                            root_dir, threads_per_process=1):
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
        catapult_vivado_tcl=Path(root_dir, 'tessera', 'tcl', 'catapult', 'vivado.tcl').resolve(),
        flags=sweep_flags,
        threads_per_process=threads_per_process,
        stages=stages,
        tools={k: str(Path(v).expanduser()) for k, v in RunConfig.load().tools.items()},
    )
