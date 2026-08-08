from framework.samples import get_rng, write_csvs
from reference.field import l1_mod_add
from sympy import randprime

def generate(design, sweep_flags, design_build_dir):
    bitwidth = design["n"]
    num_samples = sweep_flags.get("num_test_samples", 10)
    rng = get_rng()
    q = randprime(1 << (bitwidth-1), (1 << bitwidth) - 1) # TODO: temporary
        
    samples = []
    goldens = []

    max_val = ((1 << bitwidth) - 1) % q
    mid_val = (max_val // 2) % q

    # Edge cases
    samples = [
        (0, 0, q),
        (max_val, max_val, q),
        (0, max_val, q),
        (max_val, 0, q),
        (mid_val, mid_val, q)
    ]

    # Remaining random samples, distributed across sub-bitwidth ranges
    effective_samples = max(num_samples - len(samples), 0)
    if effective_samples > 0:
        sub_bitwidths = list(range(1, bitwidth + 1))
        for i in range(effective_samples):
            sub_bw = sub_bitwidths[i % len(sub_bitwidths)]
            sub_max = (1 << sub_bw) - 1
            x = rng.randint(0, sub_max) % q
            y = rng.randint(0, sub_max) % q
            samples.append((x, y, q))
    
    for x, y, q in samples:
        goldens.append((l1_mod_add(x, y, q),))
    
    write_csvs(samples, goldens, design_build_dir)
