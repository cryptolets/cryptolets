from tessera.samples import get_rng, get_modulus, write_csvs
from reference.field import modmul
from reference.redc import barrett_get_mu, mont_get_q_prime, to_mont


def generate(design, sweep_flags, design_build_dir):
    bitwidth = design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    q = get_modulus(design)
    mont = design["mred"] == "mred_mont"
    rc = mont_get_q_prime(q) if mont else barrett_get_mu(q)

    goldens = []

    max_val = q - 1
    mid_val = max_val // 2

    # Edge cases
    samples = [
        (0, 0, q, rc),
        (max_val, max_val, q, rc),
        (0, max_val, q, rc),
        (max_val, 0, q, rc),
        (mid_val, mid_val, q, rc),
    ]

    # Remaining random samples, distributed across sub-bitwidth ranges
    effective_samples = max(num_samples - len(samples), 0)
    if effective_samples > 0:
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(effective_samples):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            sub_max = (1 << sub_bw) - 1
            x = rng.randint(0, min(sub_max, max_val))
            y = rng.randint(0, min(sub_max, max_val))
            samples.append((x, y, q, rc))

    # Montgomery works in its own domain, so x*y*R^-1 on the converted operands
    # is x*y*R on the plain ones
    R = 1 << bitwidth
    for x, y, q, rc in samples:
        goldens.append(((x * y * R) % q if mont else modmul(x, y, q),))

    if mont:
        samples = [(to_mont(x, q), to_mont(y, q), q, rc) for x, y, q, rc in samples]

    write_csvs(samples, goldens, design_build_dir)
