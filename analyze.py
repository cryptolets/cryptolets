import csv
import os
import math

# things we want to extract from the tables
ATTR_TO_COL_NAME = {
    "cycles": [
        "Latency Cycle",
        "Latency Cycles",
    ],
    "period": [
        "Clock Period",
    ],
    "ii": [
        "Throughput Cycle",
        "Throughput Cycles",
    ],
    "reg": [
        "Total Reg"
    ],
    "area": [
        "Area",
        "Total Area",
    ],
    "memory": [
        "Memory",
        "Area(BRAMs)",
        "Area(RAMB18)",
        "Area(RAMB36)",
    ],
    "slack": [
        "Slack",
    ],
    "lut": [
        "Total Lut Area",
        "Area(LUTs)",
    ],
    "ff": [
        "Area(FFs)",
    ],
    "dsp": [
        "total-dsps",
        "Area(DSP)",
    ],
    "bram": [
        "Area(BRAMs)",
    ],
    "ctime": [
        "Total"
    ]
}

ASIC_TECH_TYPES = ["asic", "asicgf12", "saed32"]
FPGA_TECH_TYPES = ["fpga"]

def parse_table_csv(csv_fn):
    flows = []
    was_sep_row = False

    with open(csv_fn, mode='r') as file:
        csv_reader = csv.reader(file)
        
        # Iterate through each row in the CSV
        for row in csv_reader:
            if len(row) < 2:
                was_sep_row = True
            else:
                if was_sep_row:
                    was_sep_row = False
                    flows.append([])

                flows[-1].append(row)  # Print each row

    unfilters_attrs = []
    parsed_raw_attrs = {}
    
    for flow in flows:
        seen_sol = {"solution.v1"} # we don't care about default sol
        header = []
        unfilters_attrs.append({})

        for i, row in enumerate(flow):
            if i != 0: # row is not header
                sol_name = row[0].split()[0].strip() # filter out flow_name
                if sol_name not in seen_sol:
                    unfilters_attrs[-1][sol_name] = {}

                    # add new sol if not exists
                    if sol_name not in parsed_raw_attrs:
                        parsed_raw_attrs[sol_name] = {k:None for k in ATTR_TO_COL_NAME}

                    seen_sol.add(sol_name)

                    for j, col_val in enumerate(row):
                        if j > 1:
                            for attr, col_names in ATTR_TO_COL_NAME.items():
                                if header[j].strip() in col_names:
                                    parsed_raw_attrs[sol_name][attr] = col_val

            else: # header row
                header = row[:]

    return parsed_raw_attrs

def parse_sol_name(sol_name):    
    # bw   ->  "sol"
    # mod  ->  "sol_qt${q_type}"
    # mul  ->  "sol_bm${bm}_kar${kar}"
    # padd ->  "sol_bm${bm}_kar${kar}_qt${q_type}"

    # mp ->  starts with "sol_limbs${limbs}" instead of "sol"

    sol_name = sol_name.split(".")[0] # remove version
    parts = sol_name.split("_")
    info = {
        "limbs": None,
        "bm": None,
        "kar": None,
        "q_type": None,
    }

    if parts[0].startswith("sol_limbs"):
        info["limbs"] = int(parts[0].replace("sol_limbs", ""))

    for p in parts:
        if p.startswith("bm"):
            info["bm"] = int(p[2:])
        elif p.startswith("kar"):
            info["kar"] = int(p[3:])
        elif p.startswith("qt"):
            info["q_type"] = p[2:]
        elif p.startswith("limbs"):
            info["limbs"] = int(p.replace("limbs", ""))

    return info


def parse_table_name(table_name):
    # bw   ->  "table_bw${bitwidth}_${tech_type}_ii${target_ii}_f${period}ns.csv"
    # mod  ->  "table_bw${bitwidth}_${tech_type}_ii${target_ii}_qt${q_type}_f${period}ns.csv"
    # mul  ->  "table_bw${bitwidth}_${tech_type}_ii${target_ii}_mt${mul_type}_f${period}ns.csv"
    # padd ->  "table_bw${bitwidth}_${tech_type}_ii${target_ii}_mt${mul_type}_f${period}ns.csv"

    # mp -> starts with "table_mp_" instead of "table_
    name = table_name.replace(".csv", "")
    parts = name.split("_")
    info = {
        "bitwidth": None,
        "limbs": None,
        "wbw": None,
        "tech_type": None,
        "target_ii": None,
        "q_type": None,
        "mul_type": None,
        "target_freq": None,
        "target_period": None
    }

    for p in parts:
        if p.startswith("bw"):
            info["bitwidth"] = int(p[2:])
        elif p.startswith("ii"):
            info["target_ii"] = int(p[2:])
        elif p.startswith("qt"):
            info["q_type"] = p[2:]
        elif p.startswith("mt"):
            info["mul_type"] = p[2:]
        elif p.startswith("tt"):
            info["tech_type"] = p[2:]
        elif p.startswith("f"):
            info["target_freq"] = float(p[1:].replace("MHz", ""))
        elif p.startswith("p"):
            info["target_period"] = float(p[1:].replace("ns", ""))
        elif p.startswith("ct"):
            info["curve_type"] = name.split("_ct")[-1]

    return info

def derive_all_attr(parsed_raw_attrs, table_info):
    def to_float(val):
        return None if val in (None, "") else round(float(val), 2)

    results = []
    for sol, a in parsed_raw_attrs.items():
        cycles = round(float(a.get("cycles"))) if a.get("cycles") else None
        period = float(a.get("period")) if a.get("period") else None
        slack = float(a.get("slack")) if a.get("slack") else None
        ii, area = to_float(a.get("ii")), to_float(a.get("area"))
        sol_info = parse_sol_name(sol)
        all_info = {**table_info, **sol_info}

        period = period if period else all_info["target_period"]
        minclkprd = period-slack if (period and slack) else None
        latency = None
        if period and slack:
            if cycles > 0:
                latency = round(cycles*(period-slack), 2)
            else:
                latency = round(period-slack, 2)        

        ctime_raw = float(a.get('ctime', 0)) # total compile time

        row = {
            "sol": sol,
            "tech_type": all_info.get("tech_type", None),
            "curve_type": all_info.get("curve_type", None),
            "target_period": round(period, 2) if period else all_info["target_period"],
            "target_freq": round(1000/period, 2) if period else None,
            "bitwidth": all_info['bitwidth'],
            "q_type": all_info['q_type'],
            "mt": all_info['mul_type'],
            "bm": all_info['bm'],
            "kar": all_info['kar'],
            "limbs": all_info['limbs'],
            "wbw": all_info['bitwidth'] // all_info['limbs'] if all_info['limbs'] else None,
            "ctime_raw": ctime_raw,
            "ctime": f"{int(ctime_raw) // 60}m {int(ctime_raw) % 60}s",
            "minclkprd": round(minclkprd, 2) if minclkprd else None,
            "fmax": round(1000/minclkprd, 2) if (minclkprd and minclkprd != 0) else None,
            "cycles": cycles,
            "latency": latency,
            "ii": ii,
            "area": area,
        }

        if all_info['tech_type'] in ASIC_TECH_TYPES:
            row["reg"] = to_float(a.get("reg"))
            row["memory"] = to_float(a.get("memory"))
        elif all_info['tech_type'] in FPGA_TECH_TYPES:
            row["lut"] = to_float(a.get("lut"))
            row["ff"] = to_float(a.get("ff"))
            row["dsp"] = to_float(a.get("dsp"))
            row["bram"] = to_float(a.get("bram"))

        has_metrics = False
        for attr_k in ATTR_TO_COL_NAME:
            if (attr_k in row and attr_k != "ctime" and row[attr_k] is not None):
                has_metrics = True
                break

        if has_metrics:
            results.append(row)

    return results

def drop_none_columns(data):
    """Remove any column where all values are None across rows."""
    if not data:
        return data

    keys = list(data[0].keys())
    keep_keys = []
    for k in keys:
        if any(row[k] is not None for row in data):
            keep_keys.append(k)

    # rebuild rows with only kept keys
    new_data = [{k: row[k] for k in keep_keys} for row in data]
    return new_data

def drop_column(data, col):
    """Remove a specific column from all rows."""
    if not data:
        return data
    return [{k: v for k, v in row.items() if k != col} for row in data]

def get_tot(data, col="ctime_raw"):
    """Remove a specific column from all rows."""
    if not data:
        return data

    tot = 0

    for row in data:
        for k, v in row.items():
            if k == col:
                tot += v
    
    return tot

def filter_mp(data, mp=False):
    if mp:
        # keep only MP rows (limbs is not None)
        return [row for row in data if row.get("limbs") is not None]
    else:
        # keep only non-MP rows (limbs is None)
        return [row for row in data if row.get("limbs") is None]

def make_table_string(data):
    if not data:
        return "No data"

    keys = list(data[0].keys())
    col_widths = {k: max(len(str(k)), max(len(str(row[k])) for row in data)) for k in keys}

    # Header + separator
    header = " | ".join(f"{k:<{col_widths[k]}}" for k in keys)
    sep = "-+-".join("-" * col_widths[k] for k in keys)

    # Rows
    rows = []
    for row in data:
        line = " | ".join(f"{str(row[k]):<{col_widths[k]}}" for k in keys)
        rows.append(line)

    return "\n".join([header, sep] + rows)

def write_csv(data, filename="out.csv"):
    if not data:
        return
    keys = list(data[0].keys())
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"CSV written to {filename}")


def write_txt(data, filename="out.txt"):
    table_str = make_table_string(data)
    with open(filename, "w") as f:
        f.write(table_str + "\n")
    print(f"TXT written to {filename}")

def sort_key(row):
    # extract .v{n} at end of sol name
    vnum = int(row["sol"].split(".")[-1][1:])

    return (
        vnum,
        row.get("tech_type") or "",
        row.get("curve_type") or "",
        row.get("target_period") or float("inf"),
        row.get("ii") or float("inf"),
        row.get("q_type") or "",
        row.get("mt") or "",
        row.get("bm") or float("inf"),
        row.get("kar") or float("inf"),
        row.get("bitwidth") or float("inf"),
    )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Catapult results")
    parser.add_argument("kernel", help="Kernel path with vl (e.g., lvl0_primitives/add_f/)")
    parser.add_argument("--mp", action="store_true", help="Enable multi-precision mode")
    parser.add_argument("-a", "--asic", action="store_true", help="Target ASIC (default: FPGA)")
    parser.add_argument("-o", "--out-txt", action="store_true", help="Write TXT output")
    parser.add_argument("-c", "--out-csv", action="store_true", help="Write CSV output")
    parser.add_argument("-t", "--tech-type", action="store_true", help="Show tech type")
    parser.add_argument("--ccore", action="store_true", help="Include Catapult ccore solutions (default: only top-level sols)")
    parser.add_argument("--freq", action="store_true", help="show freq metrics")
    args = parser.parse_args()

    kernel = os.path.basename(os.path.normpath(args.kernel))
    kernel_path = args.kernel
    mp = args.mp
    tech_type = "asic" if args.asic else "fpga"

    catapult_dir = f"{kernel_path}/Catapult/"
    all_metrics = []

    if os.path.isdir(catapult_dir):
        for fn in os.listdir(catapult_dir):
            if not fn.startswith("table_"):
                continue
            
            fp = os.path.join(catapult_dir, fn)
            table_info = parse_table_name(fn)

            if not table_info["tech_type"] in ASIC_TECH_TYPES:
                continue

            all_metrics += derive_all_attr(parse_table_csv(fp), table_info)

        # filter and clean
        all_metrics = filter_mp(all_metrics, mp)
        all_metrics = sorted(all_metrics, key=sort_key)
        all_metrics = drop_none_columns(all_metrics)
        tot_ctime = get_tot(all_metrics, "ctime_raw")
        all_metrics = drop_column(all_metrics, "ctime_raw")

        if args.freq:
            all_metrics = drop_column(all_metrics, "target_period")
            all_metrics = drop_column(all_metrics, "minclkprd")
        else:
            all_metrics = drop_column(all_metrics, "target_freq")
            all_metrics = drop_column(all_metrics, "fmax")

        if not args.tech_type:
            all_metrics = drop_column(all_metrics, "tech_type")

        only_top = [row for row in all_metrics if row["sol"].startswith("sol")]
        num_runs = len(only_top)

        if not args.ccore:
            all_metrics = only_top

        # pretty print
        table_str = make_table_string(all_metrics)
        print(table_str)

        if num_runs > 0:
            ctime_fmt = lambda t: f"{int(t)//3600}h {(int(t)%3600)//60}m {int(t)%60}s"
            print("")
            print(f"Total compile time = {ctime_fmt(tot_ctime)}")
            print(f"Avg compile time = {ctime_fmt(tot_ctime / num_runs)}")
            print(f"Num of runs = {num_runs}")

        out_fn = f"{kernel}_{tech_type}" if not mp else f"{kernel}_{tech_type}_mp"
        # output dirs
        if args.out_txt:
            outdir = "results/txt"
            os.makedirs(outdir, exist_ok=True)
            fname = f"{out_fn}.txt"
            write_txt(all_metrics, os.path.join(outdir, fname))

        if args.out_csv:
            outdir = "results/csv"
            os.makedirs(outdir, exist_ok=True)
            fname = f"{out_fn}.csv"
            write_csv(all_metrics, os.path.join(outdir, fname))
    else:
        print(f"No data")
