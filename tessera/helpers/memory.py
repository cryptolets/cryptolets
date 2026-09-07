"Stop a run before the machine runs out of memory"
import os
import signal
import logging
from pathlib import Path


def free_gb():
    "Memory the machine can still hand out, cache it would reclaim included"
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024**2
    return float("inf")


def watch_memory(stop, min_free_gb):
    "Stop every tool, and this run, when the machine is nearly out of memory"
    while not stop.wait(5):
        if free_gb() < min_free_gb:
            logging.error(f"Less than {min_free_gb}G of memory left, "
                          f"stopping every tool")
            os.killpg(os.getpgid(0), signal.SIGTERM)
            return
