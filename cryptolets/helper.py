from itertools import product

def get_design_dir_name(design):
    for k, v in design.items():
        if isinstance(v, bool):
            design[k] = int(v)

    return "__".join([f"{k}_{v}" for k, v in design.items()])

def flatten_sweep(sweep):
    # TODO: We need to way to filter/override the sweep
    keys = list(sweep.keys())
    values = list(sweep.values())
    return [dict(zip(keys, combo)) for combo in product(*values)]


def unflatten_sweep(flattened_sweep):
    sweep_config = {}
    for design in flattened_sweep:
        for k, v in design.items():
            if k not in sweep_config:
                sweep_config[k] = []
            if v not in sweep_config[k]:
                sweep_config[k].append(v)
    return sweep_config