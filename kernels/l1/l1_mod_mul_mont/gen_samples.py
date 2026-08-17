from tessera.samples import get_rng, write_csvs
# TODO: import the reference function, e.g. `from reference import integer`


def generate(design, sweep_flags, design_build_dir):
    bitwidth = design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()

    max_val = (1 << bitwidth) - 1
    mid_val = max_val // 2

    samples = [
        (0, 0),
        (max_val, max_val),
        (0, max_val),
        (max_val, 0),
        (mid_val, mid_val),
    ]

    # Random fill, spread across sub-bitwidth ranges so small operands are covered
    for i in range(max(num_samples - len(samples), 0)):
        sub_max = (1 << (i % bitwidth + 1)) - 1
        samples.append((rng.randint(0, sub_max), rng.randint(0, sub_max)))

    # TODO: replace None with the reference function result
    goldens = [(None,) for _ in samples]

    write_csvs(samples, goldens, design_build_dir)
