"Small helpers the steps share"
import time
import logging


def tcl_type(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        return f'"{value}"'
    return value


def log_elapsed(tool, design_name, return_code, start_time):
    elapsed = time.time() - start_time
    hrs, mins, secs = int(elapsed // 3600), int((elapsed % 3600) // 60), elapsed % 60
    status = "COMPLETED" if return_code == 0 else "FAILED"
    log = logging.info if return_code == 0 else logging.error
    log(f"{tool} {status} for {design_name} in {hrs:d} hrs {mins:d} mins {secs:05.2f} secs")
    return return_code == 0
