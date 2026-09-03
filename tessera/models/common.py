import yaml
from pathlib import Path
from tessera.const import CURVES_FILE

def load_and_validate_yaml(model, path):
    return model.model_validate(yaml.safe_load(Path(path).read_text()))


def load_curves():
    """
    Loads curves and then reformats so 
    base and scalar fields are two keys
    """
    curves = yaml.safe_load(CURVES_FILE.read_text())

    fields = {}
    for curve, spec in curves.items():
        coeffs = {k: v for k, v in spec.items() if k not in ("base", "scalar", "desc")}
        for name in ("base", "scalar"):
            if name in spec:
                field = {**spec[name], **(coeffs if name == "base" else {})}
                fields[f"{curve}_{name}"] = field
    return fields


def is_fpga(tech_type):
    "An FPGA tech node uses fgpa prefix as convention in Tessera"
    return tech_type.startswith("fpga")
