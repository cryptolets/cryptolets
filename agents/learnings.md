# Learnings: integrate a kernel into Tessera and search its design space

This file holds lessons from one full integration of a large hierarchical kernel into Tessera, and from the design-space searches that followed. The searches had one goal: DC timing met at the target clock, then minimum area. The lessons apply to any kernel.

Sections 1 to 3 are facts about Tessera and the tools. Sections 4 to 6 are lessons for a search. Section 7 is the guardrails.

## 1. Integrate a new kernel

### 1.1 Start from the Tessera conventions

1. Create the kernel with `tessera new <kernel> <level>`. Do not create the directory by hand.
2. Copy the implementation into `impl/` of the new kernel. Then adapt it to the conventions of the existing kernels at the same level.
3. Use an existing kernel as the reference for each file: `kernel.yaml`, `impl/<kernel>_impl.h`, `<kernel>_tb.cpp`, `gen_samples.py` and `README.md`.
4. Write `gen_samples.py` in the style of the existing kernels. Put the golden math in `reference/`, not in the sample generator. Add helpers there if the reference lacks an operation.
5. Make the testbench read the CSV samples and write its outputs in the same way as the existing testbenches.
6. Reuse existing child kernels. Blackbox them in the parent with `flags.blackbox`. Pass constants to the child through its template parameters.

### 1.2 Bring up on a small configuration first

1. Before the full-size design, run a small configuration, for example a small bitwidth with a small test field. Catapult and DC then take minutes, not hours.
2. Make sure that the test parameters meet the math preconditions of the algorithm. For example, a complete formula can require a group without small torsion. A test parameter set that breaks a precondition gives false failures.
3. Climb the steps one at a time with one design: `--to cpp`, then `--to rtl`, then `--to syn`. Fix each error before you go to the next step.
4. Do the full size only after the small configuration passes `--to syn`.

### 1.3 Framework limits and the minimal changes

Keep framework changes to the minimum that the kernel needs. Do not refactor. Do not add features that the kernel does not use.

1. **Header parser.** Tessera parses the implementation header and expects one template class with a static `run` function. A kernel in another form, for example a SystemC module with several threads, does not fit. The minimal change is one opt-in flag in `kernel.yaml` (the default keeps the old behavior). When the flag is set:
   - skip the header parse.
   - generate a top file that only includes the implementation header.
   - set the Catapult top to the module class, not to its `run` function.
   - keep the class live for the compiler, so that its template is instantiated.
   - skip the combinational check, which needs the parsed header.
2. **Blackbox output names.** The blackbox code lists the child output ports for Catapult. The rules are:
   - A plain output argument `x` has the RTL port `x_rsc_dat`, and Catapult names it `x`.
   - A struct output argument `R` with field `X` has the RTL port `R_X_rsc_dat`, and Catapult names it `R.X`. Catapult rejects `R` and `R_X`.
   - Ports that end in `_triosy_lz` are handshake ports, not data. Do not list them.
   - A combinational child has plain port names with no `_rsc_dat` suffix.
3. After a change to the blackbox code, run a parent with a sequential child and a parent with a combinational child. A fix for one type can break the other.

### 1.4 Stale outputs during bring-up

1. A step does not run again for a dependency that has its `done/<step>.done` marker. A child keeps its old generated files after you change its header or generator.
2. If a child must regenerate, remove the `gen.done` marker of that child build. `--from gen` on the parent does not regenerate its dependencies.

## 2. How Tessera runs

These facts decide which commands are safe.

1. **The target kernel is always rebuilt.** Without `--resume`, Tessera runs every step in the range again for the target kernel. Dependencies are reused when their step is done.
2. **A rebuild moves the old results away.** Tessera moves the old files of the design into `<design build dir>/prior/run_<id>/`. This also occurs with `--to gen`. The reports are not deleted, but the done markers go with them, so Tessera thinks that no step is done.
3. **`--from` and `--only` reuse a stored design list.** When the range does not start at `gen`, Tessera reads the designs from `build/<kernel>/flattened_sweep_config.json`, not from the sweep file. Every run of that kernel overwrites this file. The flags still come from the sweep file.
4. **A range without `hls` drops the children.** If the range does not include `hls` (for example `--from syn` or `--from gls`), Tessera runs only the target kernel, with blackboxes off. DC then reads the children as flat RTL, with no `read_ddc` and no `dont_touch`. For a hierarchical design, use `--to syn --resume` instead (section 6).
5. **The safe pattern** is one run that ends at `rtl` or `syn`, then a second run of the same sweep file with `--to <step> --resume`. Tessera then skips the steps that have a done marker.
6. **Child period and port budget.** The period of a child is `dep_period_ratio` times the parent period, unless `deps.<child>.period` sets it. The child `io_delay` comes from `dep_io_ratio`, unless `deps.<child>.io_delay` sets it. `deps.<child>.io_delay: 0` turns the port budget off. These values are in the child design hash.
7. **Reuse a child build in a parent.** Set `deps.<child>.period` and `deps.<child>.io_delay` in the parent sweep to the exact values of the child build, and use the same child knobs. Then run `--to gen` and look for "N of N designs already built" in the log.
8. **Flags propagate.** A flag such as `syn_passes` goes to the children too, so a change makes new child builds.
9. **A combinational child alone** is timed over the period minus its `io_delay`. With a large `io_delay`, this budget is very small and the child fails alone. In the parent, the same netlist can meet timing. Judge such a child in its first sequential parent. A smaller `dep_io_ratio` gives the leaf a larger budget and a smaller netlist.

## 3. Timing and area

### 3.1 Read the reports correctly

1. A design passes only if Catapult meets timing, DC slack is 0.00 or more, and `qor.rpt` shows 0 violating paths in every path group, for setup and for hold.
2. "slack 0.00 (VIOLATED)" on a timing path is a failure.
3. `constraint.rpt` can show `min_capacitance` lines with "0.00 VIOLATED" and a `max_leakage_power` line. These are not timing paths. Use `qor.rpt` and `timing_max.rpt` for timing.
4. Sort failing paths by their start and end hierarchy: inside a child, parent to child, parent logic, and top ports. Each group needs different knobs.

### 3.2 What closed timing

1. **Catapult timing met does not mean DC timing met.** The failures were at the blackbox boundaries, where Catapult uses a fixed estimate for the child.
2. **Give a child a port budget.** A child built with `io_delay 0` uses the full cycle between its input ports and its first registers. Any parent logic in front of the child then fails. Set `deps.<child>.io_delay` to a value larger than 0. At a 1 ns clock, values from 0.15 to 0.35 ns all closed timing. Sweep three values: the latency can change with the value.
3. **One budget fix can clear other groups.** The port budget also cleared a group of parent-logic paths. The cause was not found. Run DC again after each fix before you work on the next group.
4. **Parent Catapult directives did not close parent-to-child paths.** About 18 directive variants failed. Many directives give RTL identical to the baseline.
5. **Identical RTL gives identical DC results.** Compare the RTL with the baseline before you start DC. If it is identical, do not start DC.

### 3.3 What reduced area

1. Almost all of the parent area is in the children. Area gains come from the child knobs.
2. A slightly looser child clock (`dep_period_ratio` near 1) made the child smaller and also closed child timing.
3. `RESET_CLEARS_ALL_REGS: 'no'` on the parent and the children gave about 1% less area.
4. A smaller `dep_io_ratio` made the combinational leaf netlists smaller (about 6 to 14% at the next level). The gain stopped at very small values.
5. A different internal width of the multiplier did not help. Negative or large `CLOCK_OVERHEAD` values on children changed the latency or failed Catapult timing.
6. **Catapult area is a weak proxy.** Catapult area changed by less than 1% when DC area changed by several percent. Catapult does not see the child port budget or the leaf DC area. Send a candidate to DC when its knob acts only in DC, even if its Catapult area ties with the best design.

## 4. Run times and resources

1. These times are for one large hierarchical design at about 400-bit width. Use them to plan, not as limits.
   - Large parent: Catapult about 2 h, DC about 2 h.
   - Mid-level child: DC about 70 min.
   - Leaf children: DC 5 to 45 min.
2. One full candidate (children, then parent) took 1.5 to 2 h of DC.
3. Before a large run, make sure that the machine has free cores. Other users can share the machine.

## 5. Organize a search

1. Use lanes. Give each lane one start point and its own thread budget.
2. Change one knob for each variant. Screen the variants in Catapult first. Send the useful ones to DC in a batch.
3. Stop a lane after three rounds in a row with less than 1% area gain.
4. Use a verifier that reads the reports itself and does not trust the lane result.
5. If the goal is only "pass timing", stop the other lanes when one lane has a verified pass. A lane that searches on after a pass wastes hours.
6. Put the deadline in a file as a unix time. Read it before each new candidate, so a person can extend the deadline without a restart.
7. Start each long run in the background with `nohup`. Write its log to a file, and poll with short commands.
8. Give each campaign its own build directory. Do not rename it while a run uses it, because the tool scripts hold absolute paths into it.
9. Write one CSV row for each candidate, and notes for each round. Record the knobs, cycles, Catapult area, DC area, WNS and the number of violating paths.
10. **The final step** (child check, gate-level simulation, power) uses a sweep file with only the winner, run with `--to pwr --resume`. See section 6.

## 6. Correct command patterns

1. **Send a built design to DC:** run its sweep file with `--to syn --resume`. The children then stay linked in DC as fixed blocks (`read_ddc` and `dont_touch`).
2. **Run later steps on a built design:** run its sweep file with `--to gls --resume` or `--to pwr --resume`. Tessera reads the designs from the sweep file and skips the steps that are done.
3. **Run the final step on a winner:** write a sweep file that holds only the winner, then run it with `--to pwr --resume`. Its Catapult and DC results stay in place.
4. **Make a sweep file with one design:** copy the knobs of that design into a new sweep file with no other variants. Then run `--to gen` on it only if the design has no results yet.
5. **End the search at the first verified pass when the goal is only to pass timing:** stop the other lanes, then start the final step.

## 7. Guardrails

1. Edit only the files of the search: your sweeps, notes and results. Do not edit `tessera/`, `kernels/`, `reference/`, `config.yaml` or the sweeps in `sweeps/`, unless the task is a kernel integration.
2. Do not edit test or verification files to make a design pass.
3. During a search, change only sweep knobs: sweep keys, variants, `deps`, Catapult directives and flags.
4. Do not use CLUSTER directives in any form.
5. Do not use git commands.
6. Do not read or write outside the Tessera directory.
7. Do not commit PDK files, library paths, cell names or other library content.
8. Do not run past `syn` unless the task asks for `gls` or `pwr`.
9. For a design that has results, always add `--resume`, for every step range.
10. Select the designs with the sweep file and `--resume`. Use `--from` and `--only` only when no other run of the same kernel is active.
11. Do not delete or rename anything in the build directory.
12. Do not start a parent DC run until each new child passes DC alone.
13. Obey the thread budget. Give the thread count with `-t` and the threads per process with `-p` on every run.
14. After the deadline, start no new candidates. Let the running ones finish.
15. Report a failure as a failure. Write down each departure from the plan and the reason for it.
