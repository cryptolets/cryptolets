"Generate Core Catapult Sweep files and per-design header files"
from pathlib import Path
from cryptolets.yaml_helper import *

catapult_stages = [
    # "new",
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

catapult_boilerplate = {
    "catapult_solution" : {
        "variable" : {
            "arrayname" : "var",
            "default" : {},
            "expand" : {},
        }, 
        "stages" : {},
    }
}

params_h_boilerplate = """
#ifndef PARAMS_H
#define PARAMS_H

{params}

#endif // PARAMS_H
"""

def gen_params_h(design, design_build_dir):
    params_str = ""
    for param, value in design.items():
        if isinstance(value, bool):
            value = int(value)
        params_str += f"#define {param.upper()} {value}\n"
    
    params_h_content = params_h_boilerplate.format(params=params_str)
    (design_build_dir / 'params.h').write_text(params_h_content)

def gen_catapult_yaml(sweep_conf, kernel_name, kernel_path, kernel_build_dir, root_dir):
    unflattened_sweep = sweep_conf['sweep']
    sweep_flags = sweep_conf['flags']
    sweep_params = unflattened_sweep.keys()
    yaml_variable = catapult_boilerplate['catapult_solution']['variable']
    yaml_stages = catapult_boilerplate['catapult_solution']['stages']
    kernel_yaml = yaml.safe_load(Path(kernel_path, 'kernel.yaml').read_text())

    yaml_variable['default'] = {
        "top_name": kernel_name
    }

    # Add sweep flags
    for flag, value in sweep_flags.items():
        yaml_variable['default'][flag] = value

    # Add dummy default values for each parameter
    for param in sweep_params:
        yaml_variable['default'][param] = 0

    yaml_variable['expand'] = {
        param: FlowList([v for v in unflattened_sweep[param]]) for param in sweep_params
    }

    design_name = "__".join([f"{param}_$var({param})" for param in sweep_params])

    include_paths = [
        Path(root_dir, 'cryptolets', 'cpp', 'include'),
        Path(kernel_path, 'include'),
        Path(kernel_build_dir, design_name, 'include'),
    ]
    include_paths_str = "\n".join(f"  {path.resolve()}" for path in include_paths)

    yaml_stages[f"go-pre-analyze"] = {
        "used": FlowList(sweep_params),
        "name": design_name,
        "script": LiteralStr(
            "options set Input/SearchPath {\n"+include_paths_str+"\n} -append\n"
            f"solution file add [file join {Path(kernel_path, 'src', f'{kernel_name}.cpp').resolve()}]\n"
            f"solution file add [file join {Path(kernel_path, 'src', f'{kernel_name}_tb.cpp').resolve()}] -exclude true\n"
            f"solution file add [file join {Path(root_dir, 'cryptolets', 'cpp', 'src', 'csvparser.cpp')}] -exclude true\n"
            f"solution file add [file join {Path(root_dir, 'cryptolets', 'cpp', 'src', 'tb_helper.cpp')}] -exclude true\n"
            f"solution design set $var(top_name) -top\n"
            f"solution rename {design_name}\n"
        )
    }

    for stage in catapult_stages:
        yaml_stages[f"go-{stage}"] = {"script": ""}

    yaml_stages[f"go-libraries"] = {"script": LiteralStr(
        f"run_osci_test $var(test_cpp) {kernel_build_dir.resolve() / design_name}\n" # Run C++ tests
        f"set_tech_lib $var(tech_type) {root_dir}\n"
        "set_clock $var(period)\n"
    )}

    # Add kernel specific stage scripts
    for stage in kernel_yaml['stages']:
        current_script = yaml_stages[f"go-{stage}"]['script']
        yaml_stages[f"go-{stage}"]['script'] = LiteralStr(current_script + kernel_yaml['stages'][stage])

    sweep_yaml = yaml.dump(
        catapult_boilerplate, 
        default_flow_style=False, # use block style
        sort_keys=False, # preserve order
    )
    Path(kernel_build_dir / "sweep.yaml").write_text(sweep_yaml)