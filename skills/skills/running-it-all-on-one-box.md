# Running It All on One Box

Everything runs on the machine in the room. No cloud calls, no external APIs, no fallback to a hosted model. These are the decisions that keep it that way and still make it fast.

## Placement

- Put every processing step at the lowest tier that can do the job: sensor or file source first, then the box. There is no tier above the box, so "moving it up" just means spending more of the box.
- Budget the box explicitly before building: model memory, inference threads, disk for logs and captured data, headroom for the UI.
- Write a latency target per hop before you build, then measure after the first working path. Reading a local source should be single-digit milliseconds. Anything a human is waiting on should land in tens to low hundreds of milliseconds.

## Wiring

- Pick one transport for component-to-component traffic and use it everywhere. A local pub/sub broker for streaming and events. A local HTTP call for request-response. Two at most. Three is a debugging problem you don't have time for.
- One process (or one container) per independently runnable piece. They talk over the local network, not shared files, so you can kill and restart one without killing everything.
- Decide per data stream: does it need action right now (handle on the box, immediately) or is it historical context (batch it, write it to disk)? Hot data in memory or a local file/SQLite. Nothing leaves the box.

## Models on the box

- Train or fine-tune elsewhere. Export the artifact, load it at startup. Never train during the build day and never during the demo.
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
- End-to-end p95 latency from input to visible output: write the target first, then measure; target <= 3s for anything a human waits on
- Processing components with a written tier and owner process: target 100%
- Distinct transport protocols between components: target <= 2
- Peak memory during a full run vs. available: target <= 80%
- Cold start from process launch to first useful output: target <= 60s
- Time to swap live input for a recorded replay: target <= 5 min
