#!/usr/bin/env python3
import argparse, json, pathlib, re, sys
from common import FIELD_CONTS, to_hex, compute_naf
from field_helpers import get_q_prime, get_mu, to_mont

def is_int(v): return re.fullmatch(r"-?\d+", v)
def is_bool(v): return v.lower() in {"true", "false"}
def is_float(v): return re.fullmatch(r"-?\d*\.\d+", v)

p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
p.add_argument("--json-file")
p.add_argument("--curve-type")
p.add_argument("--params", nargs="*", default=[])
a = p.parse_args()

# --- load curve constants ---
consts = {}
if a.json_file and a.curve_type:
    try:
        consts = json.load(open(a.json_file))[a.curve_type]
    except Exception:
        pass

# --- parse runtime params ---
params = {}
for pair in a.params:
    if "=" not in pair:
        continue
    k, v = pair.split("=", 1)
    v = v.strip()
    if is_float(v):
        continue
    if is_bool(v):
        v = "1" if v.lower() == "true" else "0"
    params[k.strip()] = v

# --- write header ---
out = pathlib.Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
lines = ["#ifndef TMP_PARAMS_H", "#define TMP_PARAMS_H", ""]

# Automated q_prime, mu, all mont transformations
# so we don't have to define it everywhere manually

q = int(consts.get("q", "1"), 16)
curve_bitwidth = consts.get("bitwidth", None)

for k in FIELD_CONTS:
    v = consts.get(k, "0")
    v_mont_int = to_mont(int(v, 16), q)
    v_mont = to_hex(v_mont_int)
    lines.append(f'#define FIELD_{k.upper()}_HEX "{v}"')
    lines.append(f'#define FIELD_{k.upper()}_NAF_ARR'+' {'+",".join(map(str, compute_naf(int(v, 16))))+'}')
    lines.append(f'#define FIELD_{k.upper()}_MONT_HEX "{v_mont}"')
    lines.append(f'#define FIELD_{k.upper()}_MONT_NAF_ARR'+' {'+",".join(map(str, compute_naf(v_mont_int)))+'}')

if curve_bitwidth:
    q_prime = get_q_prime(q, curve_bitwidth)
    mu = get_mu(q, curve_bitwidth)
else:
    q_prime, mu = 0, 0

lines.append(f'#define Q_HEX "{to_hex(q)}"')
lines.append('#define Q_NAF_ARR {'+",".join(map(str, compute_naf(q)))+'}')


lines.append(f'#define Q_PRIME_HEX "{to_hex(q_prime)}"')
lines.append('#define Q_PRIME_NAF_ARR {'+",".join(map(str, compute_naf(q_prime)))+'}')

lines.append(f'#define MU_HEX "{to_hex(mu)}"')
lines.append('#define MU_NAF_ARR {'+",".join(map(str, compute_naf(mu)))+'}')

for k, v in params.items():
    lines.append(f"#define {k.upper()} {v}")

lines.append("#endif // TMP_PARAMS_H\n")
out.write_text("\n".join(lines))
print(f"Generated {out}")
