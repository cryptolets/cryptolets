from tessera.samples import get_rng, write_csvs
from reference import integer


def generate(design, sweep_flags, design_build_dir):
    bitwidth = design["bitwidth"]
    skip_upper = design["skip_upper"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()

    goldens = []

    max_val = (1 << bitwidth) - 1
    mid_val = max_val // 2

    samples = [
        (0, 0),
        (max_val, max_val),
        (0, max_val),
        (max_val, 0),
        (mid_val, mid_val)
    ]

    # Remaining random samples, distributed across sub-bitwidth ranges
    effective_samples = max(num_samples - len(samples), 0)
    if effective_samples > 0:
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(effective_samples):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            sub_max = (1 << sub_bw) - 1
            samples.append((rng.randint(0, sub_max), rng.randint(0, sub_max)))

    for x, y in samples:
        goldens.append((integer.mul_par(x, y, bitwidth, skip_upper),))

    write_csvs(samples, goldens, design_build_dir)
