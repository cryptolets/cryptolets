"""
Code to take child kernels and then make them catapult blackboxes
We do this by using metrics, rtl and impl header of the child kernel.
"""
import re
import yaml

from tessera.parser.common import norm_to_cpp_conv
from tessera.templating import render


def copy_rtl(rtl, kernel_name, module, include_dir):
    """
    Copy RTL from the design's build dir into parent's blackbox dir
    The child is named to avoid conflict between multiple instances
    of the same kernel used in a parent.
    """
    renamed = re.sub(rf"\b{kernel_name}(_[a-zA-Z0-9_]+)?\b",
                     lambda m: f"{module}{m[1] or ''}", rtl.read_text())
    out = include_dir / f"{module}.v"
    out.write_text(renamed)
    return out


def gen_blackbox_headers(design, gen_only):
    include_dir = design.build_dir / "blackbox"
    include_dir.mkdir(parents=True)

    for child_name, child_designs in design.deps.items():
        designs_tmpl_ctx = []
        child_kernel = None
        
        for child_design in child_designs.values():
            package_dir = child_design.build_dir / "package"
            if not (package_dir / "manifest.yaml").exists():
                continue
            manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text())
            child_kernel = child_design.kernel

            rtl = copy_rtl(package_dir / manifest["rtl"], child_name,
                           child_design.blackbox_module, include_dir)

            tmpl_params = [{"name": f"_{p['name'].upper()}", "type": p["type"],
                            "value": norm_to_cpp_conv(child_design.design[p["name"]])}
                           for p in child_kernel.impl_spec["tmpl_params"]]

            designs_tmpl_ctx.append({
                "module": child_design.blackbox_module,
                "rtl": rtl.resolve(),
                "tmpl_params": tmpl_params,
                "ports": [p["text"] for p in child_kernel.impl_spec["run_params"]],
                "outputs": [p["name"] for p in manifest["ports"]
                            if p["direction"] == "output" and p["name"] not in ("clk", "rst")],
                "combinational": manifest["combinational"],
                "area": manifest["area"],
                "delay": manifest["delay"],
                "latency": manifest["latency"],
            })

        # Use a placeholder header if the child design is not fully built
        # Therefore, lacks complete information needed to blackbox it
        if len(designs_tmpl_ctx) != len(child_designs):
            if not gen_only:
                raise Exception(
                    f"'{child_name}' is not fully built, '{design.build_dir.name}' cannot blackbox it"
                )
            render("blackbox_todo.h.j2", include_dir / f"{child_name}_impl.h", kernel=child_name)
            continue

        impl = child_kernel.path / "impl" / f"{child_name}_impl.h"
        render(
            template="blackbox.h.j2",
            path=include_dir / f"{child_name}_impl.h",
            kernel=child_name,
            impl=str(impl.resolve()),
            designs=designs_tmpl_ctx,
        )