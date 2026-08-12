"Kernel lookup and dependency resolution"
from pathlib import Path

import yaml

KERNELS_DIR = Path('kernels')


def find_kernel(name, kernels_dir=KERNELS_DIR):
    for level in Path(kernels_dir).iterdir():
        if not level.is_dir():
            continue
        for kernel in level.iterdir():
            if kernel.name == name:
                return kernel
    raise Exception(f"Kernel '{name}' not found")


def resolve_deps(kernel_path, kernels_dir=KERNELS_DIR, _seen=None, _stack=()):
    """
    Every kernel this kernel needs, directly or through another dep.
    A kernel is always listed after the kernels it needs.
    """
    seen = [] if _seen is None else _seen
    name = Path(kernel_path).name

    if name in _stack:
        raise Exception(f"Dependency cycle: {' -> '.join((*_stack, name))}")

    kernel_yaml = yaml.safe_load(Path(kernel_path, 'kernel.yaml').read_text())
    for dep in kernel_yaml.get('deps') or []:
        dep_path = find_kernel(dep, kernels_dir)
        if dep_path in seen:
            continue
        resolve_deps(dep_path, kernels_dir, seen, (*_stack, name))
        seen.append(dep_path)

    return seen
