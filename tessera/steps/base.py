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

    def __init__(self):
        self.stages = list(self.stages) or [self.name]
        self.prev = None # the step before this one, set by the pipeline

    def done_path(self, design):
        "The marker that says this step finished for a design"
        return design.build_dir / DONE_DIR / f"{self.name}.done"

    def mark_done(self, design):
        path = self.done_path(design)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def is_done(self, design):
        return self.done_path(design).exists()

    def ready(self, design):
        "Whether the step before this one left what this one reads"
        return self.prev is None or self.prev.is_done(design)

    def setup(self, kernel, run_inst):
        "Hook for once-per-kernel work, e.g. generating the kernel tcl"
        pass

    def designs(self, designs, kernel, run_inst):
        "The designs still needing this step, narrowed by select()"
        # The requested kernel is always rebuilt, since that is the request.
        # A dependency is reused when this step already ran for it.
        if kernel.name != run_inst.target:
            todo = [d for d in designs if not self.is_done(d)]
            if len(todo) < len(designs):
                logging.info(f"{kernel.name}: {len(designs) - len(todo)} of "
                             f"{len(designs)} designs already built")
            designs = todo

        # A design the step before failed on has nothing for this one to read
        ready = [d for d in designs if self.ready(d)]
        if len(ready) < len(designs):
            logging.warning(f"{kernel.name}: skipping {len(designs) - len(ready)} "
                            f"designs that failed {self.prev.name}")

        return self.select(ready, kernel, run_inst)

    def select(self, designs, kernel, run_inst):
        "Hook to narrow the designs, e.g. to a pareto front"
        return designs

    def run(self, design, kernel, run_inst):
        "Run the step for one design, and return whether it passed"
        raise NotImplementedError

    def run_wrapper(self, design, kernel, run_inst):
        "A design that errors fails on its own, rather than ending the run"
        try:
            return self.run(design, kernel, run_inst)
        except Exception:
            logging.exception(f"{self.name} FAILED for {design.build_dir.name}")
            return False
