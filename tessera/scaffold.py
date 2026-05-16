from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).parent / "templates"

def _render(name, **subs):
    return Template((TEMPLATES_DIR / name).read_text()).safe_substitute(subs)

def new(kernel, level, force=False):
    p = Path("kernels", level, kernel)
    if p.exists() and not force:
        print(f"Kernel '{kernel}' already exists at {p}. Use --force to overwrite.")
        return

    (p / "src").mkdir(parents=True, exist_ok=True)
    (p / "include").mkdir(parents=True, exist_ok=True)

    subs = {"kernel": kernel, "kernel_upper": kernel.upper()}

    (p / "include" / f"{kernel}.h").write_text(_render("kernel.tmpl.h", **subs))
    (p / "src" / f"{kernel}.cpp").write_text(_render("kernel.tmpl.cpp", **subs))
    (p / "src" / f"{kernel}_tb.cpp").write_text(_render("kernel_tb.tmpl.cpp", **subs))
    (p / "gen_samples.py").write_text(_render("gen_samples.tmpl.py", **subs))
    (p / "kernel.yaml").write_text(_render("kernel.tmpl.yaml", **subs))
