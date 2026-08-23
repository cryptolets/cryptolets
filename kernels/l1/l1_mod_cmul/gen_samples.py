from tessera.samples import get_rng, get_modulus, write_csvs
from tessera.field import curve_coeffs
from reference.field import modmul
from reference.redc import barrett_get_mu, mont_get_q_prime, to_mont


def constant(design, q):
    "The field constant this design multiplies by"
    name = design["cmul_const"][len("cmul_"):]

    # A curve coefficient is held in the domain its reduction works in
    coeffs = curve_coeffs(design.get("curve"), q, design.get("mred") == "mred_mont")
    if name in coeffs:
        return int(coeffs[name], 16)

    return {
        "q": q,
        "q_prime": mont_get_q_prime(q),
        "mu": barrett_get_mu(q),
    }[name]


def generate(design, sweep_flags, design_build_dir):
    bitwidth = design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    q = get_modulus(design)
    mont = design["mred"] == "mred_mont"
    rc = mont_get_q_prime(q) if mont else barrett_get_mu(q)
    const = constant(design, q)

    goldens = []

    max_val = q - 1
    mid_val = max_val // 2

    # Edge cases
    samples = [
        (0, q, rc),
        (max_val, q, rc),
        (mid_val, q, rc),
    ]

    # Remaining random samples, distributed across sub-bitwidth ranges
    effective_samples = max(num_samples - len(samples), 0)
    if effective_samples > 0:
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(effective_samples):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            sub_max = (1 << sub_bw) - 1
            samples.append((rng.randint(0, min(sub_max, max_val)), q, rc))

    # Montgomery works in its own domain, so x*c*R^-1 on a converted operand
    # is x*c on the plain one
    for x, q, rc in samples:
        goldens.append((modmul(x, const, q),))

    if mont:
        samples = [(to_mont(x, q), q, rc) for x, q, rc in samples]

    write_csvs(samples, goldens, design_build_dir)
