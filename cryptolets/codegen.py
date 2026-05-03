"Generate Core Catapult Sweep files and per-design header files"
from pathlib import Path
import yaml

from cryptolets.helper import tcl_type

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

params_h_boilerplate = "#ifndef PARAMS_H\n#define PARAMS_H\n{params}\n#endif // PARAMS_H\n"

def gen_params_h(design, design_build_dir):
    params_str = ""
    for param, value in design.items():
        if isinstance(value, bool):
            value = int(value)
        params_str += f"#define {param.upper()} {value}\n"
    
    params_h_content = params_h_boilerplate.format(params=params_str)

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
        f"source {Path(root_dir, 'cryptolets', 'tcl', 'util.tcl').resolve()}",
        f"source design.tcl", # we the design directory is the working directory
    ])

    initial_lines.append("\n# Add sweep flags")
    for flag, value in sweep_conf['flags'].items():
        initial_lines.append(f"set {flag} {tcl_type(value)}")

    initial_lines.extend([
        f"\ninit_options",
        f"project new",
        f"solution rename $design_name",
    ])

    include_paths = [
        Path(root_dir, 'cryptolets', 'cpp', 'include'),
        Path(kernel_path, 'include'),
    ]
    include_paths_str = "\n".join(f"  {path.resolve()}" for path in include_paths)

    stage_lines['analyze'].extend([
        "\n# Add code files",
        "options set Input/SearchPath {\n"+include_paths_str+"\n} -append",
        f"options set Input/SearchPath [file join $design_build_dir include] -append",
        f"solution file add [file join {Path(kernel_path, 'src', f'{kernel_name}.cpp').resolve()}]",
        f"solution file add [file join {Path(kernel_path, 'src', f'{kernel_name}_tb.cpp').resolve()}] -exclude true",
        f"solution file add [file join {Path(root_dir, 'cryptolets', 'cpp', 'src', 'csvparser.cpp')}] -exclude true",
        f"solution file add [file join {Path(root_dir, 'cryptolets', 'cpp', 'src', 'tb_helper.cpp')}] -exclude true",
        f"solution design set {kernel_name}_inst -top",
    ])

    stage_lines['compile'].append(
        "\n# Add kernel specific stage directives",
    )    
    for stage in kernel_yaml['stages']:
        stage_lines[stage].extend(kernel_yaml['stages'][stage].splitlines())

    stage_lines['libraries'].extend([
        # f"run_osci_test $test_cpp $design_build_dir", # Run C++ tests
        f"set_tech_lib $tech_type $root_dir",
        f"set_clock $period"
    ])

    for stage in catapult_stages:
        stage_lines[stage].append(f"go {stage}")

    # Code to run after a stage
    for stage in ["schedule", "dpfsm", "extract"]:
        stage_lines[stage].append(f"save_table [file join $design_build_dir metrics.csv]")

    lines = initial_lines
    for stage in catapult_stages:
        lines.extend(stage_lines[stage])

    Path(kernel_build_dir / "kernel.tcl").write_text("\n".join(lines))