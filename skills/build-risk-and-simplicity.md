# Build Risk and Simplicity

Twelve hours, no slack. This is how to find the thing that will break before it breaks, and how to diagnose it in minutes instead of hours when it does anyway.

## Before you build

- Name the single riskiest technical assumption in one sentence. "It'll work" is not an assumption. "The model returns structured output we can parse without cleanup" is.
- List every layer the build touches: model runtime, drivers, camera or sensor input, audio, storage, file formats, the display, whatever wraps them. Write the assumption you're making about each. Most will feel safe.
- Spike the risky one **and the two that feel safest**. 30 minutes total, not 30 each. Builds break on the easy ground because nobody tests the easy ground.
- A spike is a question asked in code, not a prototype. It answers confirmed or falsified, then you throw it away.

## Keep it small

- Simplicity gate: could this be one script that reads a file and writes a file? If yes, do that. Every technology past the second one needs a one-sentence justification.
- Workaround test: will the person doing this manually today actually stop, on the axis they care about? Slower or more steps means they don't switch, no matter how impressive the tech is.
- Slice the build into increments of 60 minutes or less, each with a written "done" condition. First increment is the core transformation and nothing else.
- Keep a written kill list in three buckets: **kill** (new features, never build), **defer** (polish and feedback, pull back only if the demo feels dead without it), **ego** (somebody's pet feature - acknowledge, laugh, move on).
- Write the stuck protocol before you're stuck. Default: (1) is this a code problem or an environment problem? Environment problems don't respond to debugging code. (2) Reread the function line - are you still building that? (3) Simplify before adding.
- Preserve the function, change the tool. When an implementation fails, swap the library or approach without renegotiating what you're building.

## When something breaks

- **Read the actual error before forming any hypothesis.** No exceptions. This one rule is the difference between a five-minute fix and a three-hour one.
- Reproduce with the exact input first. Never diagnose from someone's description of the failure.
- Classify before touching anything:
  - **Library/API** - bad parameter, unsupported value, version mismatch
  - **Environment** - paths, env vars, drivers, model file in the wrong place, works on one machine not another
  - **Code** - an exception in a function you wrote
  - **Infra** - build failure, port conflict, permissions, disk full
- Environment is the most misdiagnosed layer. Print the actual value of the path or variable. Don't assume what's set.
- Change one variable per attempt. Change three and it works, you've learned nothing and it will happen again at hour 10.
- Verify with a real run, not a belief. If the same fix fails twice, the classification is wrong - reclassify instead of retrying.
- Generic messages ("failed to generate," "something went wrong") are caught exceptions. The real error is one layer down in the logs.

## Eval

- Assumptions spiked before the main build: target >= 3 (1 that scares you, 2 that feel safe)
- Combined spike time: target <= 30 min
- Technologies in the stack nobody can justify in one sentence: target 0
- Increments with a written done condition: target 2-10, each <= 60 min
- Kill list contents: target >= 3 kill items and >= 1 defer item
- Minutes spent guessing before reading the actual error text: target 0
- Variables changed per fix attempt: target 1
- Times the same failed fix is retried unchanged: target 0 (a second attempt means reclassify)
