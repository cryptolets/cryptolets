#!/usr/bin/env python3
import argparse
import csv
import json
import os
import random
from pathlib import Path

from ntt_sw_utils import (
    bit_rev_shuffle,
    check_ntt_modulus,
    find_ntt_modulus,
    generate_twiddle_factors,
    normalize_intt,
    ntt_naive,
)
from ntt_standard_sw_models import (
    ntt_dif_nr,
    ntt_dif_rn,
    ntt_dit_nr,
    ntt_dit_rn,
)
from ntt_constant_geometry_sw_models import (
    ntt_dif_pease,
    ntt_dit_pease,
    ntt_dif_korn_lambiotte,
    ntt_dit_korn_lambiotte,
)
from ntt_stockham_models import ntt_stockham_dif, ntt_stockham_dit

NATURAL_TO_BIT_REVERSED = {"dif_nr", "dit_nr"}
BIT_REVERSED_TO_NATURAL = {"dif_rn", "dit_rn"}

def parse_int(value):
    if value is None:
        return None
    return int(value, 0)

def get_field_const(curve_type, const_name, json_file):
    with open(json_file, "r") as f:
        value = json.load(f)[curve_type][const_name]
    if const_name == "bitwidth":
        return int(value)
    return int(value, 16)

def mod_inverse(a, m):
    old_r, r = a, m
    old_s, s = 1, 0
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
    if old_r != 1:
        raise ValueError(f"{a} has no inverse modulo {m}")
    return old_s % m

def get_q_prime(q, bitwidth):
    r = 1 << bitwidth
    return (-mod_inverse(q, r)) % r

def get_mu(q, bitwidth):
    return (1 << (2 * bitwidth)) // q

def to_mont(x, q, bitwidth):
    r = 1 << bitwidth
    return (x * r) % q

def check_ntt_size(ntt_size):
    if ntt_size < 2 or (ntt_size & (ntt_size - 1)) != 0:
        raise ValueError("NTT length must be a power of two and at least 2")

def load_modulus(bitwidth, curve_type, json_file, q_override=None, ntt_size=16, ntt_type="posicyclic", seed=42):
    if q_override is not None:
        q = q_override
    elif json_file is not None:
        q = get_field_const(curve_type, "q", json_file)
    else:
        q = find_ntt_modulus(ntt_size, bitwidth, ntt_type, seed)

    if q <= 2:
        raise ValueError("q must be an odd prime greater than 2")
    if q >= (1 << bitwidth):
        raise ValueError(f"q has bit length {q.bit_length()}, which does not fit BITWIDTH={bitwidth}")
    check_ntt_modulus(ntt_size, q, ntt_type)
    return q

def run_ntt_reference(a, q, omegas, algorithm):
    if algorithm == "naive":
        return a.copy(), ntt_naive(a, q, omegas)
    if algorithm == "dif_nr":
        return a.copy(), ntt_dif_nr(a, q, omegas)
    if algorithm == "dit_nr":
        return a.copy(), ntt_dit_nr(a, q, omegas)
    if algorithm == "dif_rn":
        a_br = bit_rev_shuffle(a)
        return a_br, ntt_dif_rn(a_br, q, omegas)
    if algorithm == "dit_rn":
        a_br = bit_rev_shuffle(a)
        return a_br, ntt_dit_rn(a_br, q, omegas)
    if algorithm == "pease_dif":
        a_br = bit_rev_shuffle(a)
        return a_br, ntt_dif_pease(a_br, q, omegas)
    if algorithm == "pease_dit":
        a_br = bit_rev_shuffle(a)
        return a_br, ntt_dit_pease(a_br, q, omegas)
    if algorithm == "korn_lambiotte_dif":
        return a.copy(), ntt_dif_korn_lambiotte(a, q, omegas)
    if algorithm == "korn_lambiotte_dit":
        return a.copy(), ntt_dit_korn_lambiotte(a, q, omegas)
    if algorithm == "stockham_dif":
        return a.copy(), ntt_stockham_dif(a, q, omegas)
    if algorithm == "stockham_dit":
        return a.copy(), ntt_stockham_dit(a, q, omegas)
    raise ValueError(f"Unsupported NTT algorithm: {algorithm}")

def run_intt_reference(intt_input, q, inverse_omegas, algorithm):
    if algorithm == "naive":
        return normalize_intt(ntt_naive(intt_input, q, inverse_omegas), q)
    if algorithm == "dif_nr":
        return normalize_intt(ntt_dif_nr(intt_input, q, inverse_omegas), q)
    if algorithm == "dit_nr":
        return normalize_intt(ntt_dit_nr(intt_input, q, inverse_omegas), q)
    if algorithm == "dif_rn":
        return normalize_intt(ntt_dif_rn(intt_input, q, inverse_omegas), q)
    if algorithm == "dit_rn":
        return normalize_intt(ntt_dit_rn(intt_input, q, inverse_omegas), q)
    if algorithm == "pease_dif":
        return normalize_intt(ntt_dif_pease(intt_input, q, inverse_omegas), q)
    if algorithm == "pease_dit":
        return normalize_intt(ntt_dit_pease(intt_input, q, inverse_omegas), q)
    if algorithm == "korn_lambiotte_dif":
        return normalize_intt(ntt_dif_korn_lambiotte(intt_input, q, inverse_omegas), q)
    if algorithm == "korn_lambiotte_dit":
        return normalize_intt(ntt_dit_korn_lambiotte(intt_input, q, inverse_omegas), q)
    if algorithm == "stockham_dif":
        return normalize_intt(ntt_stockham_dif(intt_input, q, inverse_omegas), q)
    if algorithm == "stockham_dit":
        return normalize_intt(ntt_stockham_dit(intt_input, q, inverse_omegas), q)
    raise ValueError(f"Unsupported NTT algorithm: {algorithm}")

def edge_vectors(ntt_size, q):
    vectors = [
        [0] * ntt_size,
        [1] + [0] * (ntt_size - 1),
        list(range(ntt_size)),
        [(q - 1)] * ntt_size,
    ]
    if ntt_size > 1:
        alternating = []
        for i in range(ntt_size):
            alternating.append(0 if i % 2 == 0 else q - 1)
        vectors.append(alternating)
    return [[x % q for x in v] for v in vectors]

def generate_vectors(ntt_size, q, total_samples, seed=42):
    rng = random.Random(seed)
    vectors = edge_vectors(ntt_size, q)
    while len(vectors) < total_samples:
        vectors.append([rng.randrange(0, q) for _ in range(ntt_size)])
    return vectors[:total_samples]

def convert_domain(values, q, bitwidth, use_montgomery):
    if use_montgomery:
        return [to_mont(v, q, bitwidth) for v in values]
    return values

def write_csv_files(
    bitwidth,
    ntt_size,
    total_samples,
    q,
    samples_path=None,
    golden_path=None,
    algorithm="dit_rn",
    is_modmul_mont=True,
    seed=42,
    ntt_type="posicyclic",
):
    check_ntt_size(ntt_size)
    q_prime = get_q_prime(q, bitwidth)
    mu = get_mu(q, bitwidth)
    omegas, inverse_omegas = generate_twiddle_factors(ntt_size, q, seed=seed, ntt_type=ntt_type)
    n_inv = pow(ntt_size, q - 2, q)
    vectors = generate_vectors(ntt_size, q, total_samples, seed=seed)

    samples_file = Path(samples_path) if samples_path else Path("samples") / f"samples_{bitwidth}.csv"
    golden_file = Path(golden_path) if golden_path else Path("goldens") / f"golden_{bitwidth}.csv"
    samples_file.parent.mkdir(parents=True, exist_ok=True)
    golden_file.parent.mkdir(parents=True, exist_ok=True)

    coeff_header = [f"a{i}_sample" for i in range(ntt_size)]
    omega_header = [f"omega{i}_sample" for i in range(ntt_size // 2)]
    inverse_omega_header = [f"inverse_omega{i}_sample" for i in range(ntt_size // 2)]
    redc_header_name = "q_prime_sample" if is_modmul_mont else "mu_sample"
    golden_header = (
        [f"ntt_o{i}_sample" for i in range(ntt_size)]
        + [f"intt_o{i}_sample" for i in range(ntt_size)]
    )

    redc = q_prime if is_modmul_mont else mu
    sample_rows = []
    golden_rows = []
    for a in vectors:
        ntt_input, ntt_golden = run_ntt_reference(a, q, omegas, algorithm)
        intt_golden = run_intt_reference(ntt_input, q, inverse_omegas, algorithm)
        sample_rows.append(
            convert_domain(ntt_input, q, bitwidth, is_modmul_mont)
            + convert_domain(omegas[:ntt_size // 2], q, bitwidth, is_modmul_mont)
            + convert_domain(inverse_omegas[:ntt_size // 2], q, bitwidth, is_modmul_mont)
            + convert_domain([n_inv], q, bitwidth, is_modmul_mont)
            + [q, redc]
        )
        golden_rows.append(
            convert_domain(ntt_golden, q, bitwidth, is_modmul_mont)
            + convert_domain(intt_golden, q, bitwidth, is_modmul_mont)
        )

    with samples_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            coeff_header
            + omega_header
            + inverse_omega_header
            + ["n_inv_sample", "q_sample", redc_header_name]
        )
        writer.writerows(sample_rows)

    with golden_file.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(golden_header)
        writer.writerows(golden_rows)

    print(f"Generated {samples_file} and {golden_file}")
    print(f"NTT_SIZE={ntt_size}, ntt_type={ntt_type}, algorithm={algorithm}, q={q}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate samples and golden output for NTT.")
    parser.add_argument("--bw", type=int, required=True, help="Datapath bitwidth.")
    parser.add_argument("--n", type=int, default=10, help="Number of NTT vector samples.")
    parser.add_argument("--curve_type", type=str, default="RAND_CURVE",
                        help="field_const.json key used as the modulus selector.")
    parser.add_argument("--json-file", type=str,
                        help="JSON file to get field constants from. If omitted with no --q, generate a suitable modulus.")
    parser.add_argument("--q", type=parse_int,
                        help="Override modulus as decimal or 0x-prefixed hex.")
    parser.add_argument("--ntt-size", type=int, default=16, help="NTT transform length.")
    parser.add_argument("--algorithm", type=str, default="dit_rn",
                        choices=[
                            "naive",
                            "dif_nr",
                            "dif_rn",
                            "dit_nr",
                            "dit_rn",
                            "pease_dif",
                            "pease_dit",
                            "korn_lambiotte_dif",
                            "korn_lambiotte_dit",
                            "stockham_dif",
                            "stockham_dit",
                        ],
                        help="Reference/input-output ordering variant.")
    parser.add_argument("--ntt-type", type=str, default="posicyclic",
                        choices=["posicyclic", "negacyclic"],
                        help="Root condition: posicyclic needs n | q-1; negacyclic needs 2n | q-1.")
    parser.add_argument("--samples-file", type=str, help="Optional path for samples CSV file.")
    parser.add_argument("--golden-file", type=str, help="Optional path for golden CSV file.")
    parser.add_argument("--modmul-type", type=str, default="MODMUL_TYPE_MONT",
                        help="MODMUL_TYPE_MONT emits Montgomery-domain coeffs/twiddles/goldens; otherwise normal domain.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    check_ntt_size(args.ntt_size)
    q = load_modulus(args.bw, args.curve_type, args.json_file, args.q, args.ntt_size, args.ntt_type, args.seed)
    write_csv_files(
        args.bw,
        args.ntt_size,
        args.n,
        q,
        args.samples_file,
        args.golden_file,
        args.algorithm,
        args.modmul_type == "MODMUL_TYPE_MONT",
        args.seed,
        args.ntt_type,
    )
