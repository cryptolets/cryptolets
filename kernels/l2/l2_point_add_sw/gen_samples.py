import random

from tessera.samples import get_rng, get_q, get_rc, write_csvs
from reference.ec import ShortWeierstrass
from reference.coordinates import PointInfinity


def generate(design, sweep_flags):
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    random.seed(rng.randint(0, 1 << 30)) # random_point draws from the random module

    q = get_q(design)
    rc = get_rc(design)

    field = design.structs[design.design["field"]]
    curve = ShortWeierstrass(q, int(field["a"]["val"], 16), int(field["b"]["val"], 16))

    samples, goldens = [], []
    for _ in range(num_samples):
        P = curve.random_point()
        # An equal pair takes the doubling path
        Q = P if rng.random() < 0.2 else curve.random_point()
        R = curve.add(P, Q)
        if R is PointInfinity:
            continue

        # The testbench moves the points into the Montgomery domain when the
        # design needs it, so the samples and goldens are plain
        samples.append((P.x, P.y, Q.x, Q.y, q, rc))
        goldens.append((R.x, R.y))

    write_csvs(samples, goldens, design.build_dir)
