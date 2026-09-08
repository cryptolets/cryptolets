from tessera.samples import get_rng, get_cmul_const, write_csvs
from reference import integer


def generate(design, sweep_flags):
    bitwidth = design.design["bitwidth"]
    output_type = design.design["cmul_output_type"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    const_w, const = get_cmul_const(design)

    max_val = (1 << bitwidth) - 1
    mid_val = max_val // 2

    samples = [(0,), (1,), (max_val,), (mid_val,)]
    goldens = []

    # Remaining random samples, distributed across sub-bitwidth ranges
    effective_samples = max(num_samples - len(samples), 0)
    if effective_samples > 0:
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(effective_samples):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            samples.append((rng.randint(0, (1 << sub_bw) - 1),))

    for (x,) in samples:
        goldens.append((integer.cmul(x, const, bitwidth, const_w, output_type),))

    write_csvs(samples, goldens, design.build_dir)
