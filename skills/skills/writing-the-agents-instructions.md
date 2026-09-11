# Writing the Agent's Instructions

The system prompt is a contract, not prose. The model reads every line literally, fills every gap with its own guess, and burns reasoning tokens on every contradiction.

## Clarity

- **Colleague test:** read it as a smart new hire on day one who knows nothing about the site, the data, or your team. If you'd need to ask a clarifying question to do the job, there's a gap.
- Cut the vague verbs: optimize, streamline, leverage, ensure quality, handle appropriately. Each one hides a behavior you haven't specified. Replace it with the behavior.
- Write the defaults. What does it do on malformed input? On a tool error? On a missing field? If you don't say, the model decides for you.
- Spell out sequencing. "Do X and Y" - in what order, and does Y need X's output?

## Contradiction

- Hunt for conflicting pairs: "be concise" plus "explain in detail," "always call the tool first" plus "answer simple questions immediately."
- Stronger models get *worse* with contradictions, because they spend reasoning trying to satisfy both.
- When both instructions are genuinely needed, add an explicit priority line: "when X and Y conflict, X wins."

## Completeness

- Cover the edges: empty input, zero, max and min, unexpected formats.
- Include an explicit "I don't know" path, or the model will invent an answer.
- Include an explicit escalation path, or it will either never ask for help or ask constantly.
- Specify the output format with a literal sample. "Return the data" breaks the next step in the pipeline.

## Structure

- Long reference material and data go at the top. Instructions go at the end. Models attend hardest to the beginning and the end.
- Put the single most important rule in both places.
- Group by purpose with headers or tags: output format, error handling, tool guidance. A generic "instructions" section is not a section.
- Separate fixed instructions from injected content with obvious placeholders: `{{USER_INPUT}}`, `{{SENSOR_SNAPSHOT}}`.

## Examples

- 2-3 diverse examples beat 10 similar ones: one happy path, one edge case, one messy input.
- Use realistic inputs. "User: hello / Agent: hi there" teaches nothing.
- Examples override instructions when they conflict. Check that yours demonstrate the behavior you asked for.
- More than 5 examples and the model spends attention parsing your list instead of the actual request. Convert the extras into rules.

## Fit the prompt to the model

- Small local models need explicit steering and an explicit planning instruction: "work through your approach step by step before acting."
- Strong models overtrigger on "CRITICAL: you MUST ALWAYS." Use normal, direct language.
- Prefer "consider," "evaluate," "assess" over "think" - some models treat the word as a reasoning trigger.
- For anything long-running: say what to save, where to save it, how to resume, and when to stop.
- Cut 20%. If behavior doesn't degrade, that 20% was noise. Drop the motivational preamble first.

## When it misbehaves

Reproduce with the exact input, then check in this order: contradiction, absence (did you actually specify it?), example mismatch, instruction buried in the middle of a long prompt, wrong prompt style for this model.

## Eval

- Vague words in the prompt (optimize, streamline, leverage, ensure, appropriately, as needed): target 0
- Tool-calling and failure paths with a stated default behavior: target 100%
- Contradictions found by a teammate who didn't write it: target 0
- Examples in the prompt: target 2-5, with at least 1 messy or edge input
- Output format shown as a literal sample: pass/fail
- Cut 20% of the prompt and rerun 5 test inputs; outputs that get worse: target 0 (if 0, keep the cut)
- Same input run 3 times produces the same-shape output: target 3/3
- Time for a teammate to read the prompt and correctly predict the agent's action on a test input: target <= 2 min
