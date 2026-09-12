"""
A run parameter is a port, unless the design fixes it: then its value is
baked into the hardware, read from the field struct.
"""


def is_fixed(port, design):
    return design.get(f"{port}_type") == f"fixed_{port}"


# What a fixed port bakes in, per reduction. A multiplier operand is in the
# Montgomery domain when the reduction is; q is only compared, so it is not.
FIXED_VALUE = {
    "q":  {"mred_mont": "q",       "mred_bar": "q"},
    "rc": {"mred_mont": "q_prime", "mred_bar": "mu"},
    "a":  {"mred_mont": "a_mont",  "mred_bar": "a"},
    "d":  {"mred_mont": "d_mont",  "mred_bar": "d"},
    "k":  {"mred_mont": "k_mont",  "mred_bar": "k"},
}


def fixed_member(port, design):
    "The field member a fixed port reads"
    return FIXED_VALUE[port][design["mred"]]
