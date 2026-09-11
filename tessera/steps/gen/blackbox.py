"""
Code to take child kernels and then make them catapult blackboxes
We do this by using metrics, rtl and impl header of the child kernel.
"""
import re
import yaml

from tessera.parser.common import norm_to_cpp_conv
from tessera.templating import env, render


def wrap_sequential(module, ports):
    "module <module>(args) wrapping <module>_top, x_rsc_dat -> x, pulses left open"
    data = [p for p in ports if p["name"].endswith("_rsc_dat") or p["name"] in ("clk", "rst")]
    pulses = [p["name"] for p in ports if p["name"].endswith("_triosy_lz")]
    return env.get_template("dc_wrapper.v.j2").render(module=module, data=data, pulses=pulses)


def copy_rtl(rtl, kernel_name, module, rtl_dir, combinational, ports):
    """
    Copy RTL from the design's build dir into parent's blackbox dir
    The child is named to avoid conflict between multiple instances
    of the same kernel used in a parent.
    """
    top = module if combinational else f"{module}_top"
    renamed = re.sub(rf"\b{kernel_name}(_[a-zA-Z0-9_]+)?\b",
                     lambda m: f"{module}{m[1]}" if m[1] else top, rtl.read_text())
    if not combinational:
        renamed += "\n" + wrap_sequential(module, ports)
    out = rtl_dir / f"{module}.v"
    out.write_text(renamed)
    return out


def blackbox_metrics(manifest, syn_metrics, child_design):
    """
    The area and delay Catapult plans the parent with: its own estimates for
    the child, or what DC measured once the child was synthesized
    """
    if not syn_metrics:
        return {"area": manifest["area"], "delay": manifest["delay"]}
    if manifest.get("area_dc") is None:
        raise Exception(f"bb_syn_metrics needs '{child_design.build_dir.name}' "
                        f"through syn first")
    return {"area": manifest["area_dc"], "delay": manifest["delay_dc"]}


def gen_blackbox_headers(design, run_inst):
    gen_only = run_inst.to == "gen"
    syn_metrics = run_inst.sweep_flags["bb_syn_metrics"]
    blackbox_dir = design.build_dir / "blackbox"
    impl_dir = blackbox_dir / "impl"
    rtl_dir = blackbox_dir / "rtl"
    wrapper_dir = blackbox_dir / "wrapper"
    impl_dir.mkdir(parents=True, exist_ok=True)
    rtl_dir.mkdir(parents=True, exist_ok=True)
    wrapper_dir.mkdir(parents=True, exist_ok=True)

    complete = True
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
                           child_design.blackbox_module, rtl_dir,
                           manifest["combinational"], manifest["ports"])
            if not manifest["combinational"]:
                wrapper = wrap_sequential(child_design.blackbox_module, manifest["ports"])
                (wrapper_dir / f"{child_design.blackbox_module}_wrapper.v").write_text(wrapper)

            tmpl_params = [{"name": f"_{p['name'].upper()}", "type": p["type"],
                            "value": norm_to_cpp_conv(child_design.design[p["name"]])}
                           for p in child_kernel.impl_spec["tmpl_params"]]
                           
            run_param_names = {p["name"] for p in child_kernel.impl_spec["run_params"]}
            outputs = []
            for p in manifest["ports"]:
                if p["direction"] != "output":
                    continue
                arg_name = p["name"].removesuffix("_rsc_dat")
                if arg_name in run_param_names:
                    outputs.append(arg_name)

            designs_tmpl_ctx.append({
                "module": child_design.blackbox_module,
                "rtl": rtl.resolve(),
                "tmpl_params": tmpl_params,
                "ports": [p["text"] for p in child_kernel.impl_spec["run_params"]],
                "outputs": outputs,
                "combinational": manifest["combinational"],
                "init_delay": manifest.get("params", {}).get("ii", 1),
                **blackbox_metrics(manifest, syn_metrics, child_design),
                "latency": manifest["latency"],
            })

        # Use a placeholder header if the child design is not fully built
        # Therefore, lacks complete information needed to blackbox it
        if len(designs_tmpl_ctx) != len(child_designs):
            if not gen_only:
                raise Exception(
                    f"'{child_name}' is not fully built, '{design.build_dir.name}' cannot blackbox it"
                )
            render("blackbox_todo.h.j2", impl_dir / f"{child_name}_impl.h", kernel=child_name)
            complete = False
            continue

        impl = child_kernel.path / "impl" / f"{child_name}_impl.h"
        render(
            template="blackbox.h.j2",
            path=impl_dir / f"{child_name}_impl.h",
            kernel=child_name,
            impl=str(impl.resolve()),
            designs=designs_tmpl_ctx,
        )

    return complete