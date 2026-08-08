"""
Generate Core Catapult Sweep files per-design header files
"""
from pathlib import Path
import yaml

from framework.templating import render

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
EXCLUDE_PARAMS = ['tech_type'] # Parameters that are not part of the design

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
    )


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
    kernel_src_path = Path(kernel_path, 'src')
    verify_cpp_path = Path(root_dir, 'framework', 'verify_cpp')
    verify_cpp_src_path = verify_cpp_path / 'src'
    include_paths = [
        verify_cpp_path / 'include',
        Path(kernel_path, 'include'),
    ]
    include_paths_str = "\n".join(f"  {p.resolve()}" for p in include_paths)

    analyze_stage = [
        "options set Input/SearchPath {\n" + include_paths_str + "\n} -append",
        "options set Input/SearchPath [file join $design_build_dir include] -append",
        f"solution file add [file join {(kernel_src_path / f'{kernel_name}.cpp').resolve()}]",
        f"solution file add [file join {(kernel_src_path / f'{kernel_name}_tb.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(verify_cpp_src_path / 'csvparser.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(verify_cpp_src_path / 'tb_helper.cpp').resolve()}] -exclude true",
    ]

    compile_stage = [
        f"set top_name [solution get /SOURCEHIER/FUNC_HBS/{kernel_name}<*> -match glob -return leaf]",
        "solution design set $top_name -top",
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
        catapult_util_tcl=Path(root_dir, 'framework', 'tcl', 'catapult', 'util.tcl').resolve(),
        catapult_init_tcl=Path(root_dir, 'framework', 'tcl', 'catapult', 'init.tcl').resolve(),
        catapult_verify_tcl=Path(root_dir, 'framework', 'tcl', 'catapult', 'verify.tcl').resolve(),
        flags=sweep_conf['flags'],
        stages=stages,
    )
