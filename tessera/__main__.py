from pathlib import Path
import click
import yaml
import logging

from tessera import analyze as analysis
from tessera import core
from tessera import scaffold

# Use defaults from config.yaml
RUN_CONFIG_FILE = 'config.yaml'
run_conf = yaml.safe_load(Path(RUN_CONFIG_FILE).read_text())

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
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
@click.option('--run-only', is_flag=True, default=run_conf.get('run_only', False), help='Run using existing flattened sweep configuration from build dir.')
@click.option('--dry-run', is_flag=True, default=run_conf.get('dry_run', False), help='Only generate flattened sweep configuration and exit.')
@click.option('--dc-only', 'only', flag_value='dc', default=None,
              help='Only synthesize, reusing an existing Catapult build.')
@click.option('--gls-only', 'only', flag_value='gls',
              help='Only simulate the netlist, reusing an existing synthesis.')
@click.option('--power-only', 'only', flag_value='power',
              help='Only measure power, reusing an existing simulation.')
@click.option('--gui-mode', is_flag=True, default=run_conf.get('gui_mode', False), help='Interactive GUI mode.')
def run(kernel, threads, threads_per_process, sweep, run_only, dry_run, only, gui_mode):
    core.run(
        kernel=kernel,
        threads=threads,
        threads_per_process=threads_per_process,
        sweep=sweep,
        run_only=run_only,
        dry_run=dry_run,
        only=only,
        gui_mode=gui_mode,
    )

@app.command()
@click.argument('kernel')
@click.option('--where', '-w', multiple=True, metavar='PARAM=VALUE',
              help='Only show designs with this parameter, repeatable.')
@click.option('--csv', type=click.Path(), help='Also write the rows to this file.')
@click.option('--all-columns', is_flag=True, help='Show columns that hold nothing.')
def analyze(kernel, where, csv, all_columns):
    "Show what a sweep measured, one row per design"
    filters = dict(pair.split('=', 1) for pair in where)

    rows = analysis.where(analysis.collect(Path(core.BUILD_DIR, kernel)), filters)
    if not all_columns:
        rows = analysis.drop_empty_columns(rows)
    rows = analysis.order_columns(rows)

    click.echo(analysis.table(rows))
    if rows:
        click.echo(f"\n{len(rows)} design{'s' if len(rows) > 1 else ''}")
    if csv:
        analysis.write_csv(rows, csv)
        click.echo(f"CSV written to {csv}")

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
