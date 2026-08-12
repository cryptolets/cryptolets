"Scaffold a new kernel"
from pathlib import Path
from tessera.templating import render

# Headers declare with the template parameter (_N); .cpp and testbench instantiate
# with the concrete params.h macro (N).
DEFAULT_INPUTS = [
    {"name": "x", "decl_type": "ac_int<_BITWIDTH, false>", "type": "ac_int<BITWIDTH, false>", "width": "BITWIDTH"},
    {"name": "y", "decl_type": "ac_int<_BITWIDTH, false>", "type": "ac_int<BITWIDTH, false>", "width": "BITWIDTH"},
]
DEFAULT_TEMPLATE_PARAMS = "int _BITWIDTH"
DEFAULT_TEMPLATE_ARGS = "BITWIDTH"
DEFAULT_DECL_OUTPUT_TYPE = "ac_int<_BITWIDTH+1, false>"
DEFAULT_OUTPUT_TYPE = "ac_int<BITWIDTH+1, false>"
DEFAULT_EDGE_CASES = ["0, 0", "max_val, max_val", "0, max_val", "max_val, 0", "mid_val, mid_val"]


def new(kernel, level, force=False):
    p = Path("kernels", level, kernel)
    if p.exists() and not force:
        print(f"Kernel '{kernel}' already exists at {p}. Use --force to overwrite.")
        return

    ctx = {
        "kernel": kernel,
        "inputs": DEFAULT_INPUTS,
        "template_params": DEFAULT_TEMPLATE_PARAMS,
        "template_args": DEFAULT_TEMPLATE_ARGS,
        "decl_output_type": DEFAULT_DECL_OUTPUT_TYPE,
        "output_type": DEFAULT_OUTPUT_TYPE,
        "edge_cases": DEFAULT_EDGE_CASES,
    }

    render("kernel.h.j2", p / "impl" / f"{kernel}.h", **ctx)
    render("kernel_tb.cpp.j2", p / f"{kernel}_tb.cpp", **ctx)
    render("gen_samples.py.j2", p / "gen_samples.py", **ctx)
    render("kernel.yaml.j2", p / "kernel.yaml", **ctx)
    render("README.md.j2", p / "README.md", **ctx)
