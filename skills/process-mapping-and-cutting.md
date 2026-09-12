# Process Mapping and Cutting

The build replaces something people already do by hand. Map that process first, cut it hard, then build only what survives. The gates are ordered and the order is the whole point.

**Run the short version unless you are actually re-engineering the process.** The full five gates are for redesigning a workflow you own. If the build replaces one step inside somebody else's process, which is the usual hackathon shape, you are not deleting their steps and Gate 3's deletion target has nothing to delete. In that case run Gate 1 and the bottleneck question at the end of Gate 3, stop there, and spend the saved time on the build. Twenty minutes, not ninety.

Run all five gates only when the team can name which steps it has the authority to remove. If nobody can, that is your answer.

## Gate 1: Map

- List every step from trigger to output. For each: action, owner (a person's name), touch time, wait time, what must be true before it can start.
- Touch time is work. Touch time plus wait time is the clock. The gap between them is the waste, and it is usually most of the clock.
- Steps include manual entries, phone calls, approvals, walking somewhere, waiting on a report, and handoffs between people or systems.
- If you can't name the owner of a step, you have already found a problem.

## Gate 2: Question

For each step, three questions:

- **Who put this here?** A person, not a department. "Safety requires it" is not attribution.
- **Is it still necessary?** The reason it was added may have expired.
- **What specifically happens if we skip it?** "Things might break" is not a consequence. "The next shift sees unvalidated readings" is.

Mark every step: **confirmed / unattributed / stale / vague**.

## Gate 3: Delete

- Delete in this order: unattributed, stale, vague, redundant, then confirmed-but-serving-a-secondary-goal.
- Cut aggressively, then add back what you actually miss. If you added back nothing, you didn't cut enough. Roughly 10% add-back means your cut was calibrated.
- Then find the bottleneck: the single step that caps how fast the whole thing can run. Everything before it is overproduction. Everything after it is starved.

## Gate 4: Simplify

- For each surviving step: can it merge with the next one? Can its input be simpler? Can its output be simpler so the next step parses less? Can the handoff disappear entirely?
- Do not simplify the bottleneck by making it do less. Remove friction around it - setup time, context switches, bad tools. The bottleneck's speed is the system's speed.
- If you find yourself polishing a step and realize it shouldn't exist, go back to Gate 3.

## Gate 5: Stress-test at 10x

- Ask three questions: what breaks at 10x the volume, at 1/10th the time, at 10x the variety of inputs?
- For each, name the first step that breaks and the assumption it was making.
- This finds hidden assumptions. It does not mean build for 10x.

## Rules

- Question before you delete. Delete before you simplify. Simplify before you automate. Automating a process nobody questioned is the most expensive mistake available.
- Steps that survive all five gates and are deterministic are automation candidates. Flag them. Decide during the build, not here.
- Optimizing anything that isn't the bottleneck feels productive and does nothing.

## Eval

- Mapped steps with a named human owner: target 100%
- Mapped steps with both touch time and wait time recorded: target 100%
- Percent of original steps deleted: target >= 30%
- Steps added back after deletion, as a share of deleted steps: target ~10% (0 means you under-cut)
- Steps named as the bottleneck: target exactly 1
- 10x answers written down for all three dimensions (volume, speed, variety): target 3
- Steps automated before Gate 4 finished: target 0
- Final map fits on one whiteboard photo everyone can read: pass/fail
