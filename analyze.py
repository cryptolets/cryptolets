import csv
import os
import math
from utils.naming_short import decoder

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

ASIC_TECH_TYPES = ["45nm", "gf12", "saed32", "saed14"]
FPGA_TECH_TYPES = ["fpga", "fpgahbm", "fpgahbmvhk158"]

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

def parse_dc_reports(catapult_proj_dir_fp, kernel):
    data = {}
    for d in os.listdir(catapult_proj_dir_fp):
        sol_dir = os.path.join(catapult_proj_dir_fp, d)
        if os.path.isdir(sol_dir) and d.startswith(f"{kernel}.v"):
            # QoR report
            rpt_qor = os.path.join(sol_dir, "gate_synthesis_dc", "reports", "report_qor.rpt")
            slack, area = None, None
            if os.path.isfile(rpt_qor):
                with open(rpt_qor, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("Critical Path Slack:"):
                            slack = line.split("Critical Path Slack:")[1].strip()
                        elif line.startswith("Cell Area:"):
                            area = line.split("Cell Area:")[1].strip()

            # Power report
            rpt_power = os.path.join(sol_dir, "gate_synthesis_dc", "reports", "report_power.rpt")
            total_power = None
            if os.path.isfile(rpt_power):
                with open(rpt_power, "r") as f:
                    header_found = False
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("Hierarchy"):
                            header_found = True
                            continue
                        if header_found:
                            if line.startswith("-"):  # skip separator
                                continue
                            parts = line.split()
                            if len(parts) >= 5:
                                # 0=module, 1=Switch, 2=Int, 3=Leak, 4=Total, 5=% 
                                total_power = parts[4]
                            break

            data[os.path.basename(sol_dir)] = {
                "slack": slack,
                "area": area,
                "power": total_power
            }

    return data

def parse_table_name(table_name):
    # strip prefix/suffix
    tag = table_name.replace(".csv", "").replace("table_", "")
    
    # decode using naming_short (medium-form keys)
    decoded = decoder(tag, key_type="med")

    # cast numeric values
    result = {}
    for k, v in decoded.items():
        if v is None:
            result[k] = None
            continue
        try:
            if "." in str(v):
                result[k] = float(v)
            else:
                result[k] = int(v)
        except ValueError:
            result[k] = v

    return result

def to_float(val):
    return None if val in (None, "") else round(float(val), 2)

def to_float_prec(val):
    return None if val in (None, "") else float(val)

def derive_all_attr(parsed_raw_attrs, all_info):    
    results = []
    for sol, a in parsed_raw_attrs.items():
        cycles = round(float(a.get("cycles"))) if a.get("cycles") else None
        period = to_float_prec(a.get("period"))
        slack = to_float_prec(a.get("slack"))
        power = to_float_prec(a.get("power"))
        ii, area = to_float(a.get("ii")), to_float(a.get("area"))

        period = period if period else all_info["target_period"]
        minclkprd = period-slack if (period is not None and slack is not None) else None
        latency = None
        if (period is not None and slack is not None):
            if cycles > 0:
                latency = round(cycles*(period-slack), 2)
            else:
                latency = round(period-slack, 2)        

        ctime_raw = to_float_prec(a.get("ctime")) # total compile time
        bitwidth = all_info.get('bitwidth')
        mb = all_info.get('mb', 0)
        bitwidth, masked_bw = (bitwidth - mb), bitwidth
        if bitwidth == masked_bw: masked_bw = None
        
        row = {
            "sol": sol,
            "tech_type": all_info.get("tech_type"),
            "modmul_type": all_info.get("modmul_type"),
            "curve_type": all_info.get("curve_type"),
            "a": all_info.get("a"),
            "target_period": round(period, 2) if period else all_info.get("target_period"),
            "target_freq": round(1000/period, 2) if period else None,
            "curve_pt": all_info.get('curve_pt'),
            "rc_type": all_info.get('rc_type'),
            "q_type": all_info.get('q_type'),
            "bitwidth": bitwidth,
            "masked_bw": masked_bw,
            "mt": all_info.get('mul_type'),
            "bm": all_info.get('bm'),
            "kar": all_info.get('kar'),
            "wbw": all_info.get('wbw'),
            "ctime_raw": ctime_raw if ctime_raw else 0,
            "ctime": f"{int(ctime_raw) // 60}m {int(ctime_raw) % 60}s" if ctime_raw else -1,
            "minclkprd": round(minclkprd, 2) if minclkprd else None,
            "cpr": float(all_info.get('cpr', 1)),
            "fmax": round(1000/minclkprd, 2) if (minclkprd and minclkprd != 0) else None,
            "cycles": cycles,
            "latency": latency,
            "ii": ii,
            "area": area,
            "power": f"{power:.2e}" if power else None,
        }

        if all_info.get('tech_type') in ASIC_TECH_TYPES:
            row["area (mm^2)"] = round(area/1e6, 2) if area else area
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
        # keep only MP rows (wbw is not None)
        return [row for row in data if row.get("wbw") is not None]
    else:
        # keep only non-MP rows (wbw is None)
        return [row for row in data if row.get("wbw") is None]

def find_max_area_min_latency_by_q(data):
    """
    Returns designs with min area and min latency for each q_type (fixedq and varq).
    Returns dict with keys 'fixedq' and 'varq', each containing 'min_area' and 'min_latency' designs.
    """
    results = {}
    
    for q_type in ["fixedq", "varq"]:
        filtered = [row for row in data if row.get("q_type") == q_type]
        
        min_area_row = None
        min_latency_row = None
        min_area = float('inf')
        min_latency = float('inf')
        
        for row in filtered:
            area = row.get('area')
            latency = row.get('latency')
            
            if area is not None and area < min_area:
                min_area = area
                min_area_row = row
                
            if latency is not None and latency < min_latency:
                min_latency = latency
                min_latency_row = row
        
        results[q_type] = {
            'min_area': min_area_row,
            'min_latency': min_latency_row
        }
    
    return results

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
        # vnum,
        row.get("sol") or "",
        row.get("tech_type") or "",
        row.get("modmul_type") or "",
        row.get("curve_type") or "",
        row.get("a") or "",
        # row.get("target_period") or float("inf"),
        row.get("ii") or float("inf"),
        row.get("curve_pt") or "",
        row.get("rc_type") or "",
        row.get("q_type") or "",
        row.get("bitwidth") or float("inf"),
        row.get("mt") or "",
        -row.get("bm") if row.get("bm") else float("inf"),
        -row.get("kar") if row.get("kar") else float("inf"),
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
    parser.add_argument("--proj-dir", type=str, default="Catapult", help="switch between project dirs")
    parser.add_argument("--ccore", action="store_true", help="Include Catapult ccore solutions (default: only top-level sols)")
    parser.add_argument("--freq", action="store_true", help="show freq metrics")
    parser.add_argument("--period", type=str, help="Filter results by clock period value")
    parser.add_argument("--curve", type=str, help="Filter results by curve type")
    parser.add_argument("--no-syn", action="store_true", help="Do not include synthesis results")
    args = parser.parse_args()

    kernel = os.path.basename(os.path.normpath(args.kernel))
    kernel_path = args.kernel
    mp = args.mp
    tech_type = "asic" if args.asic else "fpga"

    catapult_dir = f"{kernel_path}/{args.proj_dir}/"
    all_metrics = []

    if os.path.isdir(catapult_dir):
        for fn in os.listdir(catapult_dir):
            if not fn.startswith("table_"):
                continue
            
            fp = os.path.join(catapult_dir, fn)
            proj_sweep_key = fn.split("table_")[-1].split(".")[0]
            catapult_proj_dir_fp = os.path.join(catapult_dir, f"Catapult_{proj_sweep_key}")
            table_info = parse_table_name(fn)
            syn_raw_attrs = {}

            if tech_type == "asic" and not table_info.get("tech_type") in ASIC_TECH_TYPES:
                continue
            if tech_type == "fpga" and not table_info.get("tech_type") in FPGA_TECH_TYPES:
                continue

            if table_info["tech_type"] in ASIC_TECH_TYPES and os.path.isdir(catapult_proj_dir_fp):
                syn_raw_attrs = parse_dc_reports(catapult_proj_dir_fp, kernel)

            parsed_raw_attrs = parse_table_csv(fp)

            # override catapult data with dc reports
            if not args.no_syn:
                for sol in syn_raw_attrs:
                    for attr in syn_raw_attrs[sol]:
                        if syn_raw_attrs[sol][attr]:
                            parsed_raw_attrs[sol][attr] = syn_raw_attrs[sol][attr]

            all_metrics += derive_all_attr(parsed_raw_attrs, table_info)

        # filter and clean
        all_metrics = filter_mp(all_metrics, mp)
        all_metrics = sorted(all_metrics, key=sort_key)
        all_metrics = drop_none_columns(all_metrics)
        tot_ctime = get_tot(all_metrics, "ctime_raw")
        all_metrics = drop_column(all_metrics, "ctime_raw")

        # Filter by period as float if requested
        if args.period:
            try:
                period_val = float(args.period)
                all_metrics = [row for row in all_metrics if isinstance(row.get('target_period'), (float, int)) and abs(row.get('target_period') - period_val) < 1e-6]
            except ValueError:
                all_metrics = [row for row in all_metrics if str(row.get('target_period')) == args.period]

        # Filter by curve type if requested
        if args.curve:
            all_metrics = [row for row in all_metrics if str(row.get('curve_type')) == args.curve]

        if args.freq:
            all_metrics = drop_column(all_metrics, "target_period")
            all_metrics = drop_column(all_metrics, "minclkprd")
        else:
            all_metrics = drop_column(all_metrics, "target_freq")
            all_metrics = drop_column(all_metrics, "fmax")

        if not args.tech_type:
            all_metrics = drop_column(all_metrics, "tech_type")

        only_top = [row for row in all_metrics if row["sol"].startswith(kernel)]
        num_runs = len(only_top)

        if not args.ccore:
            all_metrics = only_top

        # pretty print
        table_str = make_table_string(all_metrics)
        print(table_str)

        # # Find and print designs with min area and min latency by q_type
        # area_latency_results = find_max_area_min_latency_by_q(all_metrics)
        # for q_type in ["fixedq", "varq"]:
        #     print(f"\nDesign with minimum area ({q_type}):")
        #     if area_latency_results[q_type]['min_area']:
        #         print(make_table_string([area_latency_results[q_type]['min_area']]))
        #     else:
        #         print("None found.")
            
        #     print(f"\nDesign with minimum latency ({q_type}):")
        #     if area_latency_results[q_type]['min_latency']:
        #         print(make_table_string([area_latency_results[q_type]['min_latency']]))
        #     else:
        #         print("None found.")

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
