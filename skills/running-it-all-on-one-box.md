# Running It All on One Box

Everything runs on the machine in the room. No cloud calls, no external APIs, no fallback to a hosted model. These are the decisions that keep it that way and still make it fast.

## The required stack

The rules list NemoClaw, OpenClaw and OpenShell as if they were three choices. They are not. They stack:

```
  OpenClaw    the agent itself - runs the loop, calls tools,
              reads and edits files, runs terminal commands
      |
  OpenShell   NVIDIA's sandbox runtime, part of the Agent Toolkit.
              Kernel-level sandboxing. A YAML policy engine declares
              what the agent may access, which tools it may call,
              which data it may read.
      |
  NemoClaw    the orchestration layer. Installs OpenShell, creates the
              sandbox, routes every inference call through policy.
              `nemoclaw.sh` installs Node, OpenShell and the CLI in one go.
```

Run `nemoclaw.sh` first, before anything else. Everything downstream assumes it.

**The policy file is how you prove rule 02, not just how you satisfy it.** The requirement is no remote LLM or API calls in the agent's runtime path. A declarative YAML policy that names the allowed surface is a thing you can put on screen in front of a judge. "We didn't call out" is a claim; the policy plus a run with the network unplugged is evidence. Budget five minutes of the demo for it.

**Decline the networked options in the setup wizard.** The NemoClaw onboarding wizard offers Brave Search and messaging channels (Telegram, Discord, Slack), and a policy tier with network presets. Every one of those is an outbound call in the runtime path. Say no at the prompt rather than turning them off later, and pick the most restrictive network preset on offer. A wizard default is the most likely way this build fails rule 02 by accident.

**The guardrails you wrote get enforced here.** `agent-architecture-and-guardrails.md` asks you to write down what the agent never does. OpenShell's policy engine is where that stops being a document and starts being enforced. Anything on the never list that is not in the policy file is still just prose.

## Know the box before you budget it

Verified specs for the Dell Pro Max with GB10, but measure on the actual machine anyway:

- **128GB LPDDR5X unified memory.** Unified means the model, the KV cache, your retrieval index and the UI all draw from the same pool. There is no separate VRAM number to fill. Budget against 128 total.
- **20-core Arm CPU plus a Blackwell GPU, running DGX OS.** Arm, not x86. Any Python wheel, binary or container without an arm64 build will fail at install time, and it will fail on the easy ground rather than the hard part. This is the first thing to spike.
- Roughly 1 PFLOP FP4, rated for models up to about 200B parameters. You will not need anything near that. Smaller and faster demos better.

## Placement

- Put every processing step at the lowest tier that can do the job: sensor or file source first, then the box. There is no tier above the box, so "moving it up" just means spending more of the box.
- Budget the box explicitly before building: model memory, inference threads, disk for logs and captured data, headroom for the UI.
- Write a latency target per hop before you build, then measure after the first working path. Reading a local source should be single-digit milliseconds. Anything a human is waiting on should land in tens to low hundreds of milliseconds.

## Wiring

- Pick one transport for component-to-component traffic and use it everywhere. A local pub/sub broker for streaming and events. A local HTTP call for request-response. Two at most. Three is a debugging problem you don't have time for.
- One process (or one container) per independently runnable piece. They talk over the local network, not shared files, so you can kill and restart one without killing everything.
- Decide per data stream: does it need action right now (handle on the box, immediately) or is it historical context (batch it, write it to disk)? Hot data in memory or a local file/SQLite. Nothing leaves the box.

## Models on the box

- **Load a stock open-weights model. Do not bring a trained artifact.** The build window rule disqualifies anything materially built before doors open, and a model you fine-tuned last week is the clearest possible example. Existing libraries and published weights are explicitly fine; a checkpoint you produced is not. If you genuinely need adaptation, do it with the prompt and with retrieval, both of which you build on the day and both of which demo better anyway.
- Never train or fine-tune during the build day either. It eats the clock and it eats the box.
- If the model is too slow or too big: quantize, prune, or drop to a smaller model before you change the architecture. Model size is the cheapest lever you have.
- Load the model once at process start, not per request. Measure the cold start separately from the steady-state latency.

## Build order and fallbacks

- Simulate the input first. Replay a CSV, a log file, or a recorded video into the pipeline. Real hardware and real sensor integration is a separate later step, and it is the first thing you cut if the clock runs out.
- Keep the input source swappable behind one interface so you can flip between live and replay in a minute.
- Security still applies offline: validate anything you parse, never evaluate input as code, and assume anyone can physically touch the box.

## Watch it while it runs

- Monitor CPU/GPU utilization, memory, thermal state, and inference latency. These are also good demo material - a live utilization readout makes the "it runs locally" claim visible.
- Alert yourself on the two that actually kill demos: memory saturation and latency creep after long runs.

## Eval

- Outbound network calls during a full run: target 0 (verify by disabling the network and rerunning)
- Full demo path completes with the network off: pass/fail
- `nemoclaw.sh` run before any other setup step: pass/fail
- Networked wizard options accepted (Brave Search, Telegram, Discord, Slack): target 0
- Guardrails from the never list that are absent from the OpenShell policy file: target 0
- Model artifacts loaded that the team produced before the event: target 0
- arm64 availability confirmed for every dependency before the main build: target 100%
- End-to-end p95 latency from input to visible output: write the target first, then measure; target <= 3s for anything a human waits on
- Processing components with a written tier and owner process: target 100%
- Distinct transport protocols between components: target <= 2
- Peak memory during a full run vs. available: target <= 80%
- Cold start from process launch to first useful output: target <= 60s
- Time to swap live input for a recorded replay: target <= 5 min
