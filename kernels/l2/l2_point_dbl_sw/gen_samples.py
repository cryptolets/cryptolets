import random

from tessera.samples import get_rng, get_q, get_rc, write_csvs
from reference.ec import ShortWeierstrass
from reference.coordinates import PointInfinity
from reference.redc import to_mont


def generate(design, sweep_flags):
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    random.seed(rng.randint(0, 1 << 30)) # random_point draws from the random module

    q = get_q(design)
    rc = get_rc(design)
    mont = design.design["mred"] == "mred_mont"

    field = design.structs[design.design["field"]]
    curve = ShortWeierstrass(q, int(field["a"]["val"], 16), int(field["b"]["val"], 16))

    samples, goldens = [], []
    for _ in range(num_samples):
        P = curve.random_point()
        R = curve.add(P, P)
        if R is PointInfinity:
            continue

        pts = [P.x, P.y]
        if mont:
            pts = [to_mont(v, q) for v in pts]
        samples.append((*pts, q, rc))
        goldens.append((to_mont(R.x, q), to_mont(R.y, q)) if mont else (R.x, R.y))

    write_csvs(samples, goldens, design.build_dir)
