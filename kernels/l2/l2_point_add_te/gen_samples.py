import random

from tessera.samples import get_rng, get_q, get_rc, write_csvs
from reference.ec import TwistedEdwards
from reference.coordinates import PointInfinity


def generate(design, sweep_flags):
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    random.seed(rng.randint(0, 1 << 30)) # random_point draws from the random module

    q = get_q(design)
    rc = get_rc(design)

    field = design.structs[design.design["field"]]
    curve = TwistedEdwards(q, int(field["a"]["val"], 16), int(field["d"]["val"], 16))

    samples, goldens = [], []
    for _ in range(num_samples):
        P, Q = curve.random_point(), curve.random_point()
        R = curve.add(P, Q)
        if R is PointInfinity:
            continue

        samples.append((P.x, P.y, Q.x, Q.y, q, rc))
        goldens.append((R.x, R.y))

    write_csvs(samples, goldens, design.build_dir)
