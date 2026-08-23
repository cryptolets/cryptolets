import random

from tessera.samples import get_rng, get_modulus, write_csvs
from reference.ec import ShortWeierstrass, TwistedEdwards
from reference.coordinates import PointInfinity
from reference.redc import barrett_get_mu, mont_get_q_prime, to_mont


def curve_of(design, q):
    "The curve this design works over, built from its own parameters"
    from tessera.config import curves
    from tessera.field import curve_coeffs
    c = curve_coeffs(design.get("curve"), q, False)
    form = curves().get(design.get("curve"), {}).get("form", "Weierstrass")
    if form == "TwistedEdwards":
        return TwistedEdwards(q, int(c["a"], 16), int(c["d"], 16))
    return ShortWeierstrass(q, int(c["a"], 16), int(c["b"], 16))


def reduction_const(design, q):
    "q_prime for montgomery, the wider mu for barrett"
    if design.get("mred") == "mred_mont":
        return mont_get_q_prime(q)
    return barrett_get_mu(q)


def generate(design, sweep_flags, design_build_dir):
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    random.seed(rng.randint(0, 1 << 30))

    q = get_modulus(design)
    curve = curve_of(design, q)
    rc = reduction_const(design, q)
    mont = design.get("mred") == "mred_mont"

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

    write_csvs(samples, goldens, design_build_dir)
