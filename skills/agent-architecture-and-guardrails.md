# Agent Architecture and Guardrails

If the build is a model in a loop that picks tools and takes actions, three things have to be written down before anyone codes: what it can do, how it decides, and what it never does.

## Tools: what it can do

For each tool, write all seven fields:

- **Name** - what the model sees in its tool list
- **Type** - read-only query, writes state, or irreversible
- **Description** - one sentence written for the model, not for a developer reading source
- **Input** - exact parameter names, types, and constraints
- **Output** - exact shape returned, including what an error looks like
- **Error behavior** - what the tool returns on failure and what the agent should do next
- **Side effects** - what changes in the world when it runs, or "none"

Rules:

- No two descriptions may overlap. If a teammate can't say which tool applies to a given request, the model can't either.
- Descriptions are prompts. Say when to use it **and** when not to: "use this for equipment history; for live readings use the other one instead."
- Return the three fields the agent needs, not fifty. Output shape is a token budget.
- Every write and every irreversible tool documents what happens when it's called wrong.

## Reasoning: how it decides

- **Name the loop** in one word: single-shot, reason-act-observe, plan-then-execute, or a state machine with named states. Unnamed means the model defaults to whatever it does naturally, which may not match the task.
- Say whether it plans before acting, whether the plan is shown to the operator, and how many steps before it pauses for confirmation.
- **Chaining:** which tool chains are expected, which are prohibited (never two writes back to back without confirmation), and the max chain depth before it stops and reports what it has.
- **State:** what it remembers across turns, what gets written to disk, when it summarizes or drops older context.
- **Model choice:** name the model and why - capability vs. speed vs. memory footprint on the box. Steer small models hard and explicitly; steer strong models lightly.

## Guardrails: what it never does

All five categories, each with at least one literal rule:

- **Input** - how it handles off-topic requests, attempts to override its instructions, and sensitive or personal data.
- **Output** - when it must say "I don't know" instead of guessing, tone limits, when it qualifies a claim instead of stating it as fact.
- **Tool** - which tools require human confirmation, which sequences are banned, max tool calls per turn.
- **Escalation** - how many failures before it hands off to a human, which actions always require a human, what it does when someone asks for a person.
- **Failure behavior** - what it does when it can't finish the job. "Return an error" is not a plan. Write the degraded path.

A vague guardrail does not exist. "Handle errors gracefully" is nothing. "After 3 failed tool calls, stop, print the last error, and show the operator the manual next step" is a guardrail.

## Eval

- Tools with all seven fields filled in: target 100%
- Tool pairs a teammate can't disambiguate from descriptions alone: target 0
- Total tools in the set: target <= 7
- Loop type named in one word: pass/fail
- Guardrail categories with at least one literal rule: target 5 of 5
- Guardrails containing a hard number (retry count, max calls, chain depth, timeout): target >= 3
- Irreversible tools with no confirmation gate: target 0
- Live check: feed 3 out-of-scope inputs, agent refuses or redirects all of them: target 3/3
