from datetime import datetime
from pathlib import Path
import click
import yaml
import logging

# from tessera import analyze as analysis
from tessera import core
from tessera.const import RUN_CONFIG_FILE, RUNS_DIR
from tessera.flows import STAGES
from tessera import scaffold

# Use defaults from config.yaml
run_conf = yaml.safe_load(Path(RUN_CONFIG_FILE).read_text())

# Set up logging, keeping each run's log beside the builds
RUNS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(),
              logging.FileHandler(RUNS_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.log")],
)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def app():
    pass

@app.command()
@click.argument('kernel')
@click.option('--threads', '-t', default=run_conf.get('total_threads', 8), type=int, help='Total number of threads.')
@click.option('--threads-per-process', '-p', default=run_conf.get('threads_per_process', 1), type=int, help='Threads per process.')
@click.option('--sweep', '-s', type=str, required=True, help='Sweep file.')
@click.option('--from', 'frm', type=click.Choice(STAGES), default=run_conf.get('frm', 'gen'),
              help='The stage to start at, reusing what an earlier run built.')
@click.option('--to', type=click.Choice(STAGES), default=run_conf.get('to', 'rtl'),
              help='The stage to stop after.')
@click.option('--only', type=click.Choice(STAGES), default=None,
              help='Run one stage alone, reusing what an earlier run built.')
@click.option('--verbose', '-v', is_flag=True, help='Show debug logging.')
def run(kernel, threads, threads_per_process, sweep, frm, to, only, verbose):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    core.run(
        kernel=kernel,
        threads=threads,
        threads_per_process=threads_per_process,
        sweep=sweep,
        frm=frm,
        to=to,
        only=only,
    )

# @app.command()
# @click.argument('kernel')
# @click.option('--where', '-w', multiple=True, metavar='PARAM=VALUE',
#               help='Only show designs with this parameter, repeatable.')
# @click.option('--csv', type=click.Path(), help='Also write the rows to this file.')
# @click.option('--all-columns', is_flag=True, help='Show columns that hold nothing.')
# @click.option('--build', default=str(core.BUILD_DIR), type=click.Path(),
#               help='Build directory to read, for keeping older runs aside.')
# def analyze(kernel, where, csv, all_columns, build):
#     "Show what a sweep measured, one row per design"
#     rows = analysis.run(kernel, where, csv, all_columns, build)

#     click.echo(analysis.table(rows))
#     if rows:
#         click.echo(f"\n{len(rows)} design{'s' if len(rows) > 1 else ''}")
#     if csv:
#         click.echo(f"CSV written to {csv}")


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
