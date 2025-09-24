#!/usr/bin/env python3
import argparse
import pathlib
import json

def main():
    parser = argparse.ArgumentParser(description="Generate tmp_params.h with constants from JSON")
    parser.add_argument("--out", required=True, help="Output file for header file")
    parser.add_argument("--curve-type", required=True, help="")
    parser.add_argument("--json-file", required=True, help="Path to JSON file with constants")
    args = parser.parse_args()

    # Load JSON values
    with open(args.json_file, "r") as f:
        data = json.load(f)

    q_hex = data[args.curve_type]["q"]
    q_prime_hex = data[args.curve_type]["q_prime"]
    mu_hex = data[args.curve_type]["mu"]

    out_file = pathlib.Path(args.out)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    content = f"""#ifndef TMP_PARAMS_H
#define TMP_PARAMS_H

#define Q_HEX "{q_hex}"
#define Q_PRIME_HEX "{q_prime_hex}"
#define MU_HEX "{mu_hex}"

#endif // TMP_PARAMS_H
"""

    out_file.write_text(content)
    print(f"Generated {out_file}")

if __name__ == "__main__":
    main()
