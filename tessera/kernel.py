"Kernel lookup and dependency resolution"
from pathlib import Path

from tessera.parse import parse_kernel

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

    The deps are the members the author declared, so the implementation is
    the only place they are written down.
    A kernel is always listed after the kernels it needs.
    """
    seen = [] if _seen is None else _seen
    name = Path(kernel_path).name

    if name in _stack:
        raise Exception(f"Dependency cycle: {' -> '.join((*_stack, name))}")

    impl_spec = parse_kernel(Path(kernel_path, 'impl', f"{name}_impl.h"))
    for dep in impl_spec['deps']:
        dep_path = find_kernel(dep['kernel'], kernels_dir)
        if dep_path in seen:
            continue
        resolve_deps(dep_path, kernels_dir, seen, (*_stack, name))
        seen.append(dep_path)

    return seen
