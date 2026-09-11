from reference.field import modmul
from reference.redc import to_mont
from tessera.samples import get_rng, get_q, get_rc, get_cmul_const, write_csvs


def generate(design, sweep_flags):
    bitwidth = design.design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    q = get_q(design)
    mont = design.design["mred"] == "mred_mont"
    rc = get_rc(design)
    _, const = get_cmul_const(design)

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

    write_csvs(samples, goldens, design.build_dir)
