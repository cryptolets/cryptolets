import logging

from tessera.const import DONE_DIR


class Step:
    """
    One step of the pipeline, run over a kernel's designs.
    """
    name = ""

    # The checkpoints --from and --to can name. Most steps are one checkpoint
    # named after the step itself; Catapult owns several.
    stages = ()

    # The license the tool checks out, so the pool is capped by what is free
    license = None

    # Catapult holds one thread per process, the rest take what they are given
    multi_threaded = True

    # A dep design already built by an earlier run is reused. Generate cannot
    # reuse, since what it writes depends on the stage range, not the design.
    skip_if_done = True

    def __init__(self):
        self.stages = list(self.stages) or [self.name]

    def done_path(self, design, kernel):
        "Write a done file to mark this step finished for a design"
        design_dir = kernel.build_dir / design.get_dir_name(kernel.config.design_key)
        return design_dir / DONE_DIR / f"{self.name}.done"

    def mark_done(self, design, kernel):
        path = self.done_path(design, kernel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def designs(self, designs, kernel, run):
        "The designs still needing this step, narrowed by select()"
        # The requested kernel is always rebuilt, since that is the request.
        # A dependency is reused when this step already ran for it.
        if self.skip_if_done and kernel.name != run.target:
            todo = [d for d in designs if not self.done_path(d, kernel).exists()]
            if len(todo) < len(designs):
                logging.info(f"{kernel.name}: {len(designs) - len(todo)} of "
                             f"{len(designs)} designs already built")
            designs = todo

        return self.select(designs, kernel, run)

    def select(self, designs, kernel, run):
        "Hook to narrow the designs, e.g. to a pareto front"
        return designs

    def run(self, design, kernel, run):
        "Run the step for one design, and return whether it passed"
        raise NotImplementedError
