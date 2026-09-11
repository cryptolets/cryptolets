from reference.field import modmul
from tessera.samples import get_rng, get_q, get_rc, write_csvs


def generate(design, sweep_flags):
    bitwidth = design.design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    q = get_q(design)
    rc = get_rc(design)

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

    # The testbench moves the operands into the Montgomery domain when the
    # design needs it, so the samples and goldens are plain
    goldens = [(modmul(x, y, q),) for x, y, q, rc in samples]
    write_csvs(samples, goldens, design.build_dir)
