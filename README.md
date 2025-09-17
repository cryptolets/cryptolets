# Cryptolets

## Setup
We need sympy for point generation, so we have a python env now.
```
python3 -m venv .venv
source .venv/bin/activate
pip install sympy
```

## Usage

You can set sweep parameters and other configs in `catapult_*_params.tcl` files.

```
bash catapult_run.sh [--dry-run] <kernel_name|all>
```
### Examples
```
bash catapult_run.sh --dry-run mul_f
bash catapult_run.sh mul_f
bash catapult_run.sh modadd
bash catapult_run.sh point_add
```

### Analyze

`analyze.py` script to track sweep progress and analyze results.

```bash
python3 analyze.py <kernel_path> [--mp] [-a] [-o] [-c] [-t] [--freq] [--ccore]
```

### Other
Have to change user specific utils/util.tcl config, such as paths to Catapult and/or Design Compiler libs and db filepaths. 

## Methodology & Recommendations

I setup the sweep params in `catapult_*_params.tcl` file.  

Then, I like to have 2 terminals split:  
- one to run `catapult_run.sh`  
- the other to run `watch -n 2 "python3 analyze.py ..."` for live view of sweep progress  

If errors occur we can explore more in `logs/` and `<lvl_dir>/<kernel>/Catapult/` project files. 