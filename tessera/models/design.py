import copy
import hashlib

from tessera.structs.field import get_field
from tessera.structs.hamming import gen_hamming_const

# We explicitly state the design params whose value is a reference to a struct
# e.g. field: "bn254_base" or cmul_const: "bn254_base-q_prime"
PARAMS_MAPPED_TO_STRUCT = {"field", "cmul_const"}

class Design:
    design: dict 
    structs: dict

    def __init__(self, design: dict):
        self.design = copy.deepcopy(design)
        self.structs = {}

    def attach_structs(self, kernel):
        """
        Fill structs with everything this design's kernel can name:
        the design's struct params, the kernel's declared fields and structs.
        """
        # The struct each struct-valued param points at. Only the root names
        # a struct; the rest of a ref is a path inside it, so
        # cmul_const: "bn254_base-q_prime" only needs bn254_base loaded.
        roots = [self.design[p].split("-")[0]
                 for p in PARAMS_MAPPED_TO_STRUCT if p in self.design]

        # Plus extra fields the kernel's impl names directly (kernel.yaml)
        for name in roots + kernel.config.fields:
            if name not in kernel.config.structs:
                # A field, from curves.yaml or generated for arb_field
                try:
                    self.structs[name] = get_field(name, self.design.get("bitwidth"))
                except KeyError:
                    raise Exception(f"unknown struct '{name}' in a design "
                                    f"for kernel '{kernel.name}'")

        # Custom structs defined in kernel.yaml
        for name, struct in kernel.config.structs.items():
            self.structs[name] = struct

        # Special case for l0_int_cmul kernel:
        # We generate a constant from the sweep's width and hamming weight
        if "cmul_hamming" in self.design:
            self.structs["cmul_const"] = gen_hamming_const(
                self.design["cmul_const_w"], self.design["cmul_hamming"])

    @staticmethod
    def _flatten_struct(prefix, struct, names):
        for key, value in struct.items():
            name = f"{prefix}__{key}"
            if isinstance(value, dict):
                Design._flatten_struct(name, value, names)
            else:
                names[name] = value

    def get_expr_vars(self):
        vars = dict(self.design)

        # A struct named directly in an arg, e.g. BN254_SCALAR::W -> bn254_scalar__w
        for name, struct in self.structs.items():
            Design._flatten_struct(name, struct, vars)

        # A struct reached through a param, e.g. _FIELD::W -> field__w
        for param in PARAMS_MAPPED_TO_STRUCT:
            if param in self.design and self.design[param] in self.structs:
                Design._flatten_struct(param, self.structs[self.design[param]], vars)

        return vars

    def get_design(self):
        return self.design

    def get_dir_name(self, design_key=None):
        """
        design's build directory name
        """
        keys = design_key or list(self.design)

        # A parameter the sweep did not give this design names nothing, so a
        # multiplier that never splits carries no base width
        parts = []
        for key in keys:
            if key not in self.design:
                continue
            value = self.design[key]
            parts.append(f"{key}_{int(value) if isinstance(value, bool) else value}")
        return "__".join(parts)

    def get_hash(self, design_key=None):
        "sha256 of the design's identity, which get_dir_name defines"
        return hashlib.sha256(self.get_dir_name(design_key).encode()).hexdigest()



if __name__ == "__main__":
    design = {
        "bitwidth": 254,
        "tech_type": "gf12_highperf",
        "period": 1.0,
        "ii": 1,
        "field": "bn254_base",
    }

    fields = [design["field"]]
    custom_constants = {
        "cmul_q": "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47",
    }

    Design(design)