import click
from pathlib import Path
import yaml

from cryptolets import core

# Use defaults from config.yaml
RUN_CONFIG_FILE = 'config.yaml'
run_conf = yaml.safe_load(Path(RUN_CONFIG_FILE).read_text())

@click.group()
def app():
    pass

@app.command()
@click.argument('kernel')
@click.option('--threads', '-t', default=run_conf.get('total_threads', 8), type=int, help='Total number of threads.')
@click.option('--threads-per-process', '-j', default=run_conf.get('threads_per_process', 1), type=int, help='Threads per process.')
@click.option('--sweep', '-s', type=str, help='Sweep file.')
@click.option('--run-only', is_flag=True, default=run_conf.get('run_only', False), help='Run using existing flattened sweep configuration from build dir.')
@click.option('--dry-run', is_flag=True, default=run_conf.get('dry_run', False), help='Only generate flattened sweep configuration and exit.')
@click.option('--rtl', default=run_conf.get('rtl_file', 'rtl'), help='select RTL file format.')
@click.option('--gui', is_flag=True, default=run_conf.get('gui_mode', False), help='Interactive GUI mode.')
def run(kernel, threads, threads_per_process, sweep, run_only, dry_run, rtl, gui):
    core.run(
        kernel=kernel,
        threads=threads,
        threads_per_process=threads_per_process,
        sweep=sweep,
        run_only=run_only,
        dry_run=dry_run,
        rtl=rtl,
        gui=gui,
    )

@app.command()
@click.argument('kernel')
def analyze(kernel):
    pass

def main():
    app()

if __name__ == "__main__":
    main()
