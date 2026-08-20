from tessera.samples import get_rng, get_modulus, write_csvs
from reference.redc import barrett_get_mu, mont_get_q_prime
from reference import integer

def constant(design):
    "The field constant this design multiplies by"
    q = get_modulus(design)
    return {
        "cmul_q": q,
        "cmul_q_prime": mont_get_q_prime(q),
        "cmul_mu": barrett_get_mu(q),
    }[design["cmul_const"]]


def generate(design, sweep_flags, design_build_dir):
    bitwidth = design["bitwidth"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    const = constant(design)
    cmul_const = design["cmul_const"]

    goldens = []

    # Barrett reduces a double width value, so its input is twice as wide
    in_width = 2 * bitwidth if cmul_const == "cmul_mu" else bitwidth
    max_val = (1 << in_width) - 1
    mid_val = max_val // 2

    samples = [(0,), (1,), (max_val,), (mid_val,)]

    # Remaining random samples, distributed across sub-bitwidth ranges
    effective_samples = max(num_samples - len(samples), 0)
    if effective_samples > 0:
        sub_bitwidths = list(range(1, in_width + 1))
        for i in range(effective_samples):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            samples.append((rng.randint(0, (1 << sub_bw) - 1),))

    for (x,) in samples:
        goldens.append((integer.cmul(x, const, cmul_const, bitwidth),))

    write_csvs(samples, goldens, design_build_dir)
