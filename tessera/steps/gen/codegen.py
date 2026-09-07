"""
Generate Core Catapult Sweep files per-design header files
"""
from pathlib import Path

from tessera.models.config import RunConfig
from tessera.models.sweep import Sweep
from tessera.templating import render
from tessera.parser.common import norm_to_cpp_conv, strip_tmpl_prefix
from tessera.models.design import PARAMS_MAPPED_TO_STRUCT
from tessera.const import DWARE_DIR, HW_CONSTRAINTS_PARAMS, KERNELS_DIR

CATAPULT_STAGES = [
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


def gen_params_h(design):
    enums = {
        norm_to_cpp_conv(value): i
        for values in Sweep.enums().values()
        for i, value in enumerate(values)
    }

    defines, usings = {}, {}
    for param, value in design.design.items():
        # Constraints steer the tools, not the C++, so they stay out of params.h
        if param in HW_CONSTRAINTS_PARAMS:
            continue
        if param in PARAMS_MAPPED_TO_STRUCT:
            # A struct ref becomes a type alias, e.g.
            # using CMUL_CONST = BN254_BASE::Q_PRIME
            # Therefore its uses the "using" syntax
            usings[norm_to_cpp_conv(param)] = norm_to_cpp_conv(value)
        else:
            # rest are define macros
            defines[norm_to_cpp_conv(param)] = norm_to_cpp_conv(value)

    render(
        "params.h.j2",
        design.build_dir / 'include' / 'params.h',
        enums=enums,
        params=defines,
        usings=usings,
        structs=design.structs,
    )


# Ports a design can fix, mapped to the param and value that fix them
FIXABLE_PORTS = {
    "q": ("q_type", "fixed_q"),
    "rc": ("redc_type", "fixed_rc")
}


def gen_kernel_top(design, kernel, combinational=False):
    """
    Generate the top header and the source file Catapult synthesizes.
    A combinational kernel is wrapped, a sequential one is the top itself.
    """
    template_args = ", ".join(p["name"].upper()
                              for p in kernel.impl_spec["tmpl_params"])

    ports, args = [], []
    for param in kernel.impl_spec["run_params"]:
        fixed_by, fixed_value = FIXABLE_PORTS.get(param["name"], (None, None))
        if fixed_by and design.design.get(fixed_by) == fixed_value:
            args.append(f"FIELD::{param['name'].upper()}::VALUE()")
            continue

        # A template param _X resolves through the params.h name X at the top
        text = strip_tmpl_prefix(param["text"])
        ports.append({"name": param["name"], "text": text})
        args.append(param["name"])

    ctx = dict(
        kernel=kernel.name,
        ports=ports,
        args=args,
        combinational=combinational,
        template_args=template_args,
    )

    render("kernel_top.h.j2", design.build_dir / 'include' / f'{kernel.name}_top.h', **ctx)
    render("kernel.cpp.j2", design.build_dir / 'src' / f'{kernel.name}_top.cpp', **ctx)
    

def gen_catapult_design_tcl(design, kernel, comb_chk=False, combinational=False):
    # Add the design's tech node, lib paths and config from config.yaml
    tech = RunConfig.load().tech[design.design['tech_type']].model_dump()
    tech = {k: str(Path(v).expanduser()) if v and k.endswith(('_path', '_file')) else (v or "")
            for k, v in tech.items()}

    render(
        "design.tcl.j2",
        design.build_dir / "design.tcl",
        design_name=design.build_dir.name,
        design_build_dir=design.build_dir.resolve(),
        design=design.design,
        tech=tech,
        comb_chk=comb_chk,
        uses_blackboxes=design.uses_blackboxes,
        top_class=f"{kernel.name}_top" if combinational else kernel.name,
    )


def _stage_bodies(kernel, run_inst):
    "Kernel-agnostic TCL per stage, before kernel.yaml additions are appended"
    cpp_path = Path(run_inst.root_dir, 'tessera', 'cpp')
    cpp_src_path = cpp_path / 'src'

    # Every kernel's impl dir is on the search path, so any dep's header
    # resolves without walking the dependency tree
    include_paths = [
        cpp_path / 'include',
        *sorted(KERNELS_DIR.glob("*/*/impl")),
    ]
    include_paths_str = "\n".join(f"  {p.resolve()}" for p in include_paths)

    analyze_stage = [
        # The blackbox dir comes first, so a generated header shadows the
        # kernel's own when that dep is blackboxed.
        "options set Input/SearchPath [file join $design_build_dir blackbox] -append",
        "options set Input/SearchPath {\n" + include_paths_str + "\n} -append",
        "options set Input/SearchPath [file join $design_build_dir include] -append",
        "solution file add [file join $design_build_dir src " + f"{kernel.name}_top.cpp]",
        # A generated header stands in for its dep only under this flag, and
        # falls back to the real implementation without it
        "if { $uses_blackboxes } { options set Input/CompilerFlags "
        "\"[options get Input/CompilerFlags] -DBLACKBOX_FLOW\" }",
        f"solution file add [file join {(kernel.path / f'{kernel.name}_tb.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(cpp_src_path / 'csvparser.cpp').resolve()}] -exclude true",
        f"solution file add [file join {(cpp_src_path / 'tb_helper.cpp').resolve()}] -exclude true",
    ]

    compile_stage = [
        # A combinational kernel is wrapped, so the top class differs
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


def gen_catapult_kernel_tcl(flags, kernel, run_inst):
    bodies = _stage_bodies(kernel, run_inst)
    for stage, body in kernel.config.stages.items():
        bodies.setdefault(stage, []).extend(body.splitlines())

    stages = [
        {
            'name': stage,
            'body': "\n".join(bodies.get(stage, [])),
            'save_table': stage in SAVE_TABLE_STAGES,
        }
        for stage in CATAPULT_STAGES
    ]

    tcl_dir = Path(run_inst.root_dir, 'tessera', 'tcl', 'catapult')
    render(
        "kernel.tcl.j2",
        kernel.build_dir / "kernel.tcl",
        root_dir=run_inst.root_dir,
        kernel_name=kernel.name,
        dware_dir=DWARE_DIR,
        catapult_util_tcl=(tcl_dir / 'util.tcl').resolve(),
        catapult_init_tcl=(tcl_dir / 'init.tcl').resolve(),
        catapult_verify_tcl=(tcl_dir / 'verify.tcl').resolve(),
        catapult_vivado_tcl=(tcl_dir / 'vivado.tcl').resolve(),
        flags=flags,
        threads_per_process=run_inst.threads_per_process,
        stages=stages,
        tools={k: str(Path(v).expanduser()) for k, v in RunConfig.load().tools.items()},
    )
