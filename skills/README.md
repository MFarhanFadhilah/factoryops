# Read Me First

Eight method files for a twelve-hour build on the Dell Pro Max with GB10. They are checklists, not code. Nothing here is part of the submission; the system gets built on the day, on the box.

## The three rules that disqualify you

1. **Built on the day, on the box.** Starter scaffolds and existing libraries are fine. Anything materially built before doors open is disqualified, including a fine-tuned model or code written beforehand.
2. **All inference local.** No remote LLM or API call in the agent's runtime path. Required stack: NemoClaw, OpenShell, OpenClaw. They compose rather than compete, see `running-it-all-on-one-box.md`.
3. **A real business workflow.** Operations, sales, support, knowledge, devops, research. Toy demos, joke projects and personal-assistant clones are not judged.

## Read in this order

```
BEFORE CODE          problem-scoping.md              who hurts, one function
                     process-mapping-and-cutting.md  short version unless
                                                     you own the process

DESIGN               agent-architecture-and-guardrails.md   tools, loop, limits
                     writing-the-agents-instructions.md     the system prompt
                     retrieval-over-documents.md            the corpus, chunks,
                                                            citations
                     gmp-policy-gate.md                     what the agent may
                                                            do, who signs,
                                                            what gets logged

BUILD                running-it-all-on-one-box.md    stack, placement, latency
                     build-risk-and-simplicity.md    spikes, kill list, debugging

END OF DAY           proving-it-works-and-pitching-it.md   the number, the five
                                                           minutes
```

`build-risk-and-simplicity.md` is the one to reread mid-afternoon when something breaks. Its debugging section is the highest-value page in the folder at hour seven.

## The clock

```
 0:00  ┌─ SETUP ──────────── run nemoclaw.sh. confirm the box.
       │                     spike arm64 on every dependency.
 0:20  ├─ SCOPE ──────────── pain sentence, one function line.
       │                     locked, not negotiable after this.
 1:05  ├─ MAP ────────────── short version. 20 min.
 1:25  ├─ SPIKES ─────────── riskiest assumption + 2 that feel safe.
 1:55  ├─ DESIGN ─────────── tools, loop, guardrails. system prompt v1.
 2:55  ├─ INGEST ─────────── five documents. one query answering.
 3:15  │
       │  ███ BUILD ███████  5 increments, ~55 min each.
       │                     this block is the flex zone.
 8:00  ├─ MEASURE ────────── run the 20-case test set.
 9:00  ├─ FIX ────────────── whatever missed threshold.
10:00  ├─ FALLBACK ──────── record the demo video. play it once.
10:30  ├─ PITCH ─────────── argument, then slides.
11:30  ├─ REHEARSE ──────── out loud, timed.
12:00  └─ SUBMIT
```

**Buffer is thirty minutes and it lives at the end.** If you are behind at 8:00 you cut scope from the build block, never from MEASURE, FALLBACK or PITCH. A working build nobody can demo scores below a smaller build with a clean five minutes. That trade feels wrong at hour eight and it is correct every time.

## Who checks the evals

Every file ends with an Eval block of numeric targets. They are the point of the folder and they are worthless unread.

- **Read them at the gate exit, not at the end.** When a block on the clock finishes, open that file's Eval and score it before starting the next one. Two minutes.
- **The person who did the work does not score it.** The other one reads the targets out loud and asks for the number. Self-scoring turns a target into a formality.
- **A missed target is a decision, not a failure.** Fix it, or write down that you accepted it and why. What you cannot do is not notice.
- Targets are calibration, not law. If one is wrong for this build, say so at the time and move on. Silently ignoring it is the failure.

## Where things go

- `pitch-notes.md` is empty on purpose. It is where the pitch lands at 10:30, built from the last section of `proving-it-works-and-pitching-it.md`.
- `research/` is market and use-case work done beforehand. It is not the system and it is not part of the build. Keep it visibly separate so the build window rule is never a question.
- `research/Type-of-data.md` holds the corpus tiers the retrieval skill depends on. Read it alongside `retrieval-over-documents.md`, not instead of it.
