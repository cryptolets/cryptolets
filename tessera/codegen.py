"Generate Core Catapult Sweep files and per-design header files"
from pathlib import Path
import yaml

from tessera.helper import tcl_type

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

params_h_boilerplate = """#ifndef PARAMS_H
#define PARAMS_H

// Enums
{enums}

// Parameters
{params}
#endif // PARAMS_H\n"""

EXCLUDE_PARAMS = ['tech_type']

def gen_params_h(design, enums, design_build_dir):
    enum_str = ""
    for enum, values in enums.items():
        if enum in EXCLUDE_PARAMS: continue
        for i, value in enumerate(values):
            enum_str += f"#define {value.upper()} {i}\n"
    
    params_str = ""
    for param, value in design.items():
        if param in EXCLUDE_PARAMS: continue
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, str):
            value = value.upper()
        params_str += f"#define {param.upper()} {value}\n"
    
    params_h_content = params_h_boilerplate.format(enums=enum_str, params=params_str)

    kernel_include_dir = Path(design_build_dir, 'include')
    kernel_include_dir.mkdir(parents=True, exist_ok=True)
    (kernel_include_dir / 'params.h').write_text(params_h_content)


def gen_catapult_design_tcl(design, design_name, design_build_dir):
    lines = [
        f"set design_name {design_name}",
        f"set design_build_dir {design_build_dir.resolve()}",
    ]

    for param, value in design.items():
        lines.append(f"set {param} {tcl_type(value)}")

    Path(design_build_dir / "design.tcl").write_text("\n".join(lines))


def gen_catapult_kernel_tcl(sweep_conf, kernel_name, kernel_path, kernel_build_dir, root_dir):
    initial_lines = []
    stage_lines = {stage: [] for stage in catapult_stages}
    kernel_yaml = yaml.safe_load(Path(kernel_path, 'kernel.yaml').read_text())

    initial_lines.extend([
        f"set root_dir {root_dir}",
        f"set kernel_name {kernel_name}",
        f"source {Path(root_dir, 'tessera', 'tcl', 'util.tcl').resolve()}",
        f"source design.tcl", # we the design directory is the working directory
    ])

    initial_lines.append("\n# Add sweep flags")
    for flag, value in sweep_conf['flags'].items():
        initial_lines.append(f"set {flag} {tcl_type(value)}")

    initial_lines.extend([
        f"\ninit_options",
        f"project new",
        f"solution rename {kernel_name}__$design_name",
    ])

    include_paths = [
        Path(root_dir, 'tessera', 'cpp', 'include'),
        Path(kernel_path, 'include'),
        
        # # TODO: temporary
        # Path('/home/gk2657/tessera/kernels/lvl0_primitives/bigint_add/include'),
        # Path('/home/gk2657/tessera/kernels/lvl0_primitives/bigint_sub/include'),
    ]
    include_paths_str = "\n".join(f"  {path.resolve()}" for path in include_paths)

    stage_lines['analyze'].extend([
        "\n# Add code files",
        "options set Input/SearchPath {\n"+include_paths_str+"\n} -append",
        f"options set Input/SearchPath [file join $design_build_dir include] -append",
        f"solution file add [file join {Path(kernel_path, 'src', f'{kernel_name}.cpp').resolve()}]",
        f"solution file add [file join {Path(kernel_path, 'src', f'{kernel_name}_tb.cpp').resolve()}] -exclude true",
        f"solution file add [file join {Path(root_dir, 'tessera', 'cpp', 'src', 'csvparser.cpp')}] -exclude true",
        f"solution file add [file join {Path(root_dir, 'tessera', 'cpp', 'src', 'tb_helper.cpp')}] -exclude true",
        # "solution file add [file join /home/gk2657/tessera/kernels/lvl0_primitives/bigint_add/src/bigint_add.cpp]",
        # "solution file add [file join /home/gk2657/tessera/kernels/lvl0_primitives/bigint_sub/src/bigint_sub.cpp]",
        # "project save",
        # "exit 0"
    ])

    stage_lines['compile'].extend([
        f"set top_name [solution get /SOURCEHIER/FUNC_HBS/{kernel_name}<*> -match glob -return leaf]",
        f"solution design set $top_name -top",
        "\n# Kernel agnostic stage directives",
        "directive set -DESIGN_GOAL latency",
        "directive set -OUTPUT_REGISTERS false",
        "directive set -OPT_CONST_MULTS full",
        "\n# Kernel specific stage directives",
    ])    
    for stage in kernel_yaml['stages']:
        stage_lines[stage].extend(kernel_yaml['stages'][stage].splitlines())

    stage_lines['libraries'].extend([
        f"run_osci_test $test_cpp $test_cpp_only $design_build_dir", # Run C++ tests
        f"set_tech_lib $tech_type $root_dir",
        f"set_clock $period"
    ])

    for stage in catapult_stages:
        stage_lines[stage].append(f"go {stage}")

    # Code to run after a stage
    for stage in ["schedule", "dpfsm", "extract"]:
        stage_lines[stage].append(f"save_table [file join $design_build_dir metrics.csv]")

    for stage in catapult_stages:
        stage_lines[stage].append(f"project save")

    lines = initial_lines
    for stage in catapult_stages:
        lines.extend(stage_lines[stage])

    Path(kernel_build_dir / "kernel.tcl").write_text("\n".join(lines))