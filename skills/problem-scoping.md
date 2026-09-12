# Problem Scoping

Before anyone writes code, the team needs one sentence about whose pain this fixes and one function that fixes it. This is the 45 minutes that saves the other 11 hours.

## The three rules that disqualify you

Check these before the pain statement, because failing one makes everything after it worthless.

- **Built on the day, on the box.** The agent and the system around it get built during the event, on the provided machine. Starter scaffolds and existing libraries are fine. Anything materially built beforehand is disqualified, and that includes a model you fine-tuned and code you wrote last week. Research, market analysis and written method are not the system, so they are fine; keep them visibly separate from the build anyway.
- **All inference local.** No remote LLM or API call anywhere in the agent's runtime path. See `running-it-all-on-one-box.md` for the required stack and how to prove this rather than claim it.
- **A real business workflow.** Operations, sales, support, knowledge, devops or research. Toy demos, joke projects and personal-assistant clones are not judged at all. The test is whether a named person at a real company is paid to do this today.

The pain-statement rules below will filter out a toy by accident. Do not rely on that. Ask the question directly: is someone paid to do this today, and would their manager notice if it stopped?

## Lock the pain

- Write it in one sentence: **"[Who] loses [how much] doing [what task] because [root cause]."**
- "Who" is a named role at a real site (line supervisor, rig floor hand, maintenance planner), not "operators" or "the plant."
- "How much" is a number with a unit: minutes per shift, dollars per incident, errors per week. No number means you don't know the pain yet.
- "Root cause" is a structural problem, not a missing feature. "They don't have a dashboard" is a solution wearing a pain costume.
- Banned words in the pain statement: streamline, optimize, leverage, enable, seamless, visibility. They hide the absence of a specific problem.

## Pressure-test it

- **Who has this at 10x?** Not who agrees the problem exists. Who is losing real money or real time today. Nodding is not adoption.
- **What is the one axis where you are undeniably better?** Faster, works with no network, no data leaves the site, one screen instead of five. One phrase. "Generally better" loses to whatever they already use.
- **What are you explicitly saying no to?** Name the users you refuse to serve and the features you won't build. If it doesn't feel painful, you haven't focused.
- Write down what evidence would prove the pain isn't real, then spend 10 minutes looking for it. Cheaper now than at hour 9.

## Compress to one function

- Write it as a single line: `function_name(painful_input) -> useful_output`.
- No UI, no auth, no database, no integrations in that line. Those are decisions for later, if at all.
- If you need the word "and" to describe what it does, that's two projects pretending to be one. Split it and pick one.
- Write the bet in one sentence: "If this ships, [who] will [observable behavior] instead of [current workaround]."
- The function signature is the scope anchor for the rest of the day. Parameters can change. The signature can't, without a team decision.

## Reset triggers

- Audience is a category ("plants," "field crews") instead of a person you can describe.
- The pain statement is a rephrased feature request.
- Someone is choosing frameworks, databases, or deploy targets before the function line exists.

## Eval

- Pain statement is one sentence and names a specific role: pass/fail
- Banned words in the pain statement (streamline, optimize, leverage, enable, seamless, visibility): target 0
- Numbers with units in the pain statement: target >= 1
- Items on the explicit "not building this" list: target >= 3
- Occurrences of "and" in the one-function description: target 0
- Function written as one line with a named input and a named output: pass/fail
- Minutes from kickoff to locked function signature: target <= 45
- Teammates who can state the pain sentence from memory: target = all of them
