from pathlib import Path
import click
import yaml
import logging

from framework import core
from framework import scaffold

# Use defaults from config.yaml
RUN_CONFIG_FILE = 'config.yaml'
run_conf = yaml.safe_load(Path(RUN_CONFIG_FILE).read_text())

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

@click.group()
def app():
    pass

@app.command()
@click.argument('kernel')
@click.option('--threads', '-t', default=run_conf.get('total_threads', 8), type=int, help='Total number of threads.')
@click.option('--threads-per-process', '-p', default=run_conf.get('threads_per_process', 1), type=int, help='Threads per process.')
@click.option('--sweep', '-s', type=str, help='Sweep file.')
@click.option('--run-only', is_flag=True, default=run_conf.get('run_only', False), help='Run using existing flattened sweep configuration from build dir.')
@click.option('--dry-run', is_flag=True, default=run_conf.get('dry_run', False), help='Only generate flattened sweep configuration and exit.')
@click.option('--gui-mode', is_flag=True, default=run_conf.get('gui_mode', False), help='Interactive GUI mode.')
def run(kernel, threads, threads_per_process, sweep, run_only, dry_run, gui_mode):
    core.run(
        kernel=kernel,
        threads=threads,
        threads_per_process=threads_per_process,
        sweep=sweep,
        run_only=run_only,
        dry_run=dry_run,
        gui_mode=gui_mode,
    )

@app.command()
@click.argument('kernel')
def analyze(kernel):
    pass

@app.command()
@click.argument('kernel')
@click.argument('level')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing kernel.')
def new(kernel, level, force):
    scaffold.new(kernel, level, force)

def main():
    app()

if __name__ == "__main__":
    main()
