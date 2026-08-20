from tessera.samples import get_rng, get_modulus, write_csvs
from reference.field import modmul_mont
from reference.redc import mont_get_q_prime


def generate(design, sweep_flags, design_build_dir):
    bitwidth = design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    q = get_modulus(design)
    q_prime = mont_get_q_prime(q)

    goldens = []

    max_val = q - 1
    mid_val = max_val // 2

    # Edge cases
    samples = [
        (0, 0, q, q_prime),
        (max_val, max_val, q, q_prime),
        (0, max_val, q, q_prime),
        (max_val, 0, q, q_prime),
        (mid_val, mid_val, q, q_prime),
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
            samples.append((x, y, q, q_prime))

    for x, y, q, q_prime in samples:
        goldens.append((modmul_mont(x, y, q, q_prime),))

    write_csvs(samples, goldens, design_build_dir)
