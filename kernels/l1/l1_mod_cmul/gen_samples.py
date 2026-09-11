from reference.field import modmul
from reference.redc import from_mont
from tessera.samples import get_rng, get_q, get_rc, get_cmul_const, write_csvs


def generate(design, sweep_flags):
    bitwidth = design.design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    q = get_q(design)
    rc = get_rc(design)
    _, const = get_cmul_const(design)

    # The testbench moves x into the Montgomery domain and the result out of
    # it, so the constant the design bakes in is read as a plain value too
    if design.design["mred"] == "mred_mont":
        const = from_mont(const, q)

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

    goldens = [(modmul(x, const, q),) for x, q, rc in samples]
    write_csvs(samples, goldens, design.build_dir)
