from cryptolets.gen_samples_helper import get_rng, write_csvs
from reference import bigint

def generate(design, design_build_dir):
    bitwidth = design["bitwidth"]
    num_samples = design.get("num_test_samples", 1000)
    rng = get_rng()
        
    samples = []
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
            x = rng.randint(0, sub_max)
            y = rng.randint(0, sub_max)
            samples.append((x, y))
    
    for x, y in samples:
        goldens.append((bigint.add(x, y),))
    
    write_csvs(samples, goldens, design_build_dir)