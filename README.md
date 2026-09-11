# FactoryOps

A maintenance-technician copilot that answers fault-code questions from
a plant's own manuals and repair history — running fully offline on a
Dell GB10, with **no cloud calls, no internet, ever, during the demo.**

## Required stack (fixed by competition rules — do not substitute)

```text
GitHub  →  Dell GB10 host  →  local Ollama model (qwen3:4b)
        →  NemoClaw  →  OpenShell sandbox  →  OpenClaw agent
```

| Component | Role |
|---|---|
| GitHub | Stores this repo: app code, data, manuals |
| Ollama | Runs the local LLM |
| qwen3:4b | The model that answers FactoryOps questions — **loaded from `load/factoryops-kit/`, never pulled with `ollama pull` on the Dell** |
| NemoClaw | Installer/manager for the agent + sandbox stack |
| OpenShell | Kernel-level sandbox that constrains the agent's file/network access |
| OpenClaw | The agent that runs inside the sandbox and answers questions |
| FactoryOps (this repo) | The manuals, repair history, and tools the agent reads |

## Repo structure

```text
factoryops/
├── README.md              this file
├── factory-ops-brief.md   market/positioning research (background reading)
├── requirements.txt
├── .env.example
├── .gitignore
├── app/                   empty skeleton (.gitkeep) — see "Building the app/tools code" below
├── tools/                 empty skeleton (.gitkeep) — see "Building the app/tools code" below
├── data/
│   └── repair_history.csv
├── manuals/
│   ├── fault_code_catalog.md
│   └── lockout_tagout_sop.md
├── load/                  gitignored — paste factoryops-kit here, see Step 2
│   └── factoryops-kit/
│       ├── model-backup/  separate qwen3:4b and qwen3:8b Ollama backups
│       └── demo/demo-script.md
└── skills/skills/         process/agent-design notes used while building this
```

`app/` and `tools/` are currently empty skeleton folders (just a
`.gitkeep` each) — no code has been written yet. See "Building the
app/tools code" below for what needs to be created and in what shape
before Steps 9–10 will work.

Every command below is run from the repo root and resolves paths off
`$(pwd)` — nothing to hand-edit, no mount points to hunt for.

---

## 1. Clone the repo

```bash
git clone https://github.com/MFarhanFadhilah/factoryops.git
cd factoryops
```

## 2. Paste `factoryops-kit` into `load/`

`load/` already exists in the repo. Plug in your flashdisk, copy the
`factoryops-kit` folder, and paste it straight into `load/` — no
command needed, just copy-paste. End result: `load/factoryops-kit/`.

`load/`'s contents are gitignored — nothing you paste in gets
committed, and it's the only thing you need to re-paste on a fresh
clone.

## 3. Check Dell GB10 prerequisites

```bash
nvidia-smi
df -h ~
docker --version && docker info >/dev/null && echo "DOCKER READY"
node --version
npm --version
```

If `docker info` fails on permissions:
```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

If the organizers preconfigured this machine, don't change NVIDIA
driver, Docker, or network policy without asking a mentor.

## 4. Start the local model — from `load/`, not `ollama pull`

**Competition rule: the model is loaded from `factoryops-kit`, never
pulled on the Dell.** Ollama is the primary runtime (NemoClaw's Local
Ollama provider expects it); llamafile is a secondary fallback only if
ollama can't run on the demo hardware — don't run both at once, they'll
fight over the same GPU/RAM.

```bash
sudo systemctl stop ollama 2>/dev/null || true
export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/4b"
ollama serve
```
Leave that terminal running. In a second terminal:
```bash
ollama list
ollama run qwen3:4b "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl http://127.0.0.1:11434/api/tags
```
Expect exactly `FACTORYOPS LOCAL MODEL READY` back. Do not stop ollama
after this test succeeds — leave it running for the rest of setup.

To use the 8B backup instead, stop the running Ollama server, point
`OLLAMA_MODELS` at the separate 8B directory, and start it again:

```bash
sudo systemctl stop ollama 2>/dev/null || true
export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/8b"
ollama serve
```

In a second terminal:

```bash
ollama run qwen3:8b
```

The current kit contains the 4B backup only; copy the 8B Ollama
`blobs/` and `manifests/` directories into
`load/factoryops-kit/model-backup/ollama/8b/` before using it.

Fallback (llamafile, only if ollama can't run here):
```bash
LLAMAFILE="$(pwd)/load/factoryops-kit/model-backup/llamafile/Qwen3.5-0.8B-Q8_0.llamafile"
sha256sum "$LLAMAFILE"   # should be ec7c3ab7903accb1b4d890cfd1fc670fabc642dcb4896735bd69d46b2629408d
chmod +x "$LLAMAFILE"
"$LLAMAFILE" --server --nobrowser
```
Serves an OpenAI-compatible API at `http://127.0.0.1:8080`. It's a
portable executable (APE) that runs unmodified on both x86_64 and the
GB10's ARM64 — no rebuild needed.

If the GB10 target is genuinely a fresh machine (no `load/` copy
possible at all), install ollama natively there instead of copying a
binary — `curl -fsSL https://ollama.com/install.sh | sh` — the *model
data* under `model-backup/ollama/` is architecture-independent and
safe to copy as-is; only the `ollama` binary itself is not.

## 5. Install NemoClaw

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
source ~/.bashrc
nemoclaw --version
nemoclaw agents list      # OpenClaw should be listed
nemoclaw host probe
```

If onboarding gets interrupted partway: `nemoclaw onboard --resume`.
Don't reinstall drivers/Docker without organizer approval.

## 6. Create the sandbox: NemoClaw + OpenShell + OpenClaw

```bash
PROJECT_DIR="$(pwd -P)"
nemoclaw onboard
```

In the wizard, choose:
```text
Agent runtime:          OpenClaw
Sandbox name:           factoryops
Inference provider:     Local Ollama
Model:                  qwen3:4b
Project host folder:    $PROJECT_DIR (the absolute path printed above)
Sandbox project folder: /sandbox/factoryops
Project mount mode:     Read-only
Web search:             Disabled
Cloud inference:        Disabled
External API keys:      None
Network policy:         Local-only / deny Internet
```

Use the wizard rather than raw CLI flags — they change between
NemoClaw versions. Don't clone separate OpenClaw/OpenShell repos;
`nemoclaw onboard` manages both.

## 7. Verify the sandbox and repo mount

```bash
nemoclaw factoryops status
nemoclaw factoryops connect
```

Inside the sandbox:
```bash
pwd
ls -la /sandbox/factoryops
head -n 5 /sandbox/factoryops/data/repair_history.csv
cat /sandbox/factoryops/manuals/lockout_tagout_sop.md
awk '$2 == "/sandbox/factoryops" { print $2, $4 }' /proc/mounts   # should include "ro"
exit
```

If the repo isn't visible in the sandbox: don't reinstall everything.
Re-check `PROJECT_DIR="$(pwd -P)"` is an **absolute** path (not `~`),
then re-run `nemoclaw onboard` with that exact path as the host mount
source and `/sandbox/factoryops` read-only as the target.

## 8. Test OpenClaw

```bash
nemoclaw factoryops connect
openclaw tui
```

Sanity check:
```text
Reply exactly: FACTORYOPS OPENCLAW READY.
```

Project-read check:
```text
Read /sandbox/factoryops/README.md.
Reply in exactly one sentence describing this project.
Do not use web search or any external network.
```

FactoryOps scenario (uses the real M4-E17 fault data already in this
repo — see `load/factoryops-kit/demo/demo-script.md` for the full
live-demo choreography):
```text
You are a FactoryOps maintenance assistant.

Use only these local files:
- /sandbox/factoryops/data/repair_history.csv
- /sandbox/factoryops/manuals/fault_code_catalog.md
- /sandbox/factoryops/manuals/lockout_tagout_sop.md

For fault code M4-E17:
1. State likely causes supported by local files.
2. State mandatory lockout/tagout steps before inspection.
3. Give a short inspection checklist.
4. State when to escalate to a supervisor.
5. Do not use the internet.
6. Do not invent facts absent from local files.
```

A good answer cites the local files, applies the LOTO safety step
before any inspection instruction, and doesn't invent anything not in
`manuals/` or `data/repair_history.csv`.

Exit: `/exit` (or Ctrl+C), then `exit` to leave the sandbox.

## 9. Run the FactoryOps UI (on the host)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8501
```
Open `http://localhost:8501`. OpenClaw keeps running inside its
sandbox as the agent/security layer regardless of where the UI runs.

## Building the app/tools code

`app/` and `tools/` ship empty (skeleton only, tracked with
`.gitkeep`) — nothing here is implemented yet. Before Steps 9–10 work,
create:

```text
app/
├── main.py         Streamlit UI — entry point for `streamlit run app/main.py`
├── local_llm.py    client for the local Ollama model (talks to http://127.0.0.1:11434)
└── retrieval.py     search over data/repair_history.csv and manuals/*.md

tools/
├── search_manuals.py       search manuals/*.md for a fault code / keyword
├── get_repair_history.py   query data/repair_history.csv
└── safety_gate.py          enforce LOTO/safety checks before returning inspection steps
```

Create the empty files (drop the now-redundant `.gitkeep`s in the same
step):

```bash
touch app/main.py app/local_llm.py app/retrieval.py
touch tools/search_manuals.py tools/get_repair_history.py tools/safety_gate.py
rm -f app/.gitkeep tools/.gitkeep
```

Implement these against the data already in the repo
(`data/repair_history.csv`, `manuals/fault_code_catalog.md`,
`manuals/lockout_tagout_sop.md`) and the local model started in Step 4
— no cloud calls.

## 10. Editing during the event

Edit on the **host**, not inside the read-only sandbox mount:
```bash
nano app/main.py   # or your editor of choice
```
Verify the sandbox sees the change:
```bash
nemoclaw factoryops connect
head -n 30 /sandbox/factoryops/app/main.py
exit
```
Checkpoint locally as you go:
```bash
git add -A && git commit -m "Hackathon demo checkpoint"
```
Push only if both network access and hackathon rules allow it.

---

## Troubleshooting

**Ollama not running / model missing**
Re-run Step 4. If it errors saying no model store found, `load/factoryops-kit/model-backup/ollama` is missing — re-copy it (Step 2). Do
not run `ollama pull` as a workaround.

**Docker permission error**
```bash
sudo usermod -aG docker "$USER" && newgrp docker
docker info
```

**NemoClaw onboarding interrupted**
```bash
nemoclaw onboard --resume
```

**Sandbox/OpenClaw unhealthy**
```bash
nemoclaw factoryops status
nemoclaw host probe
```
Don't delete the sandbox without a backup/permission — agent state
lives inside it.

**Repo not visible in the sandbox**
Re-confirm `PROJECT_DIR="$(pwd -P)"` is absolute, then re-run
`nemoclaw onboard` with that path as the host mount source.

**Internet gets disabled for the live demo**
That's expected and fine, as long as everything below was already done
beforehand:
- model already running from `load/factoryops-kit/` (Step 4)
- repo already cloned, `load/` already pasted
- Python deps already installed (`pip install -r requirements.txt`)
- NemoClaw sandbox already created (`nemoclaw onboard` completed)

Run the checklist below with the network still on, *then* cut it for
the actual demo.

## Final demo checklist

```text
[ ] Repo cloned, load/factoryops-kit/ pasted in (Step 2)
[ ] ollama serve runs against load/factoryops-kit/model-backup/ollama, ollama list shows qwen3:4b
[ ] qwen3:4b answers the local test prompt
[ ] NemoClaw CLI installed (nemoclaw --version)
[ ] nemoclaw onboard created the factoryops sandbox (OpenShell + OpenClaw)
[ ] nemoclaw factoryops status is healthy
[ ] /sandbox/factoryops shows the real repo, mounted read-only
[ ] OpenClaw answers the M4-E17 scenario citing local files
[ ] OpenClaw response includes the LOTO safety step before inspection guidance
[ ] No cloud inference, API key, or web search used anywhere
[ ] Streamlit UI runs at localhost:8501
[ ] Full path re-tested with the network off
[ ] Code changes committed locally
```

## Cheat sheet

```bash
# Clone, then paste factoryops-kit from your flashdisk into load/
git clone https://github.com/MFarhanFadhilah/factoryops.git && cd factoryops

# Start the model (NOT ollama pull)
sudo systemctl stop ollama 2>/dev/null || true
export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/4b"
ollama serve
# second terminal:
ollama run qwen3:4b "Reply exactly: FACTORYOPS LOCAL MODEL READY"

# NemoClaw
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
source ~/.bashrc
PROJECT_DIR="$(pwd -P)"
nemoclaw onboard        # OpenClaw + OpenShell + Local Ollama, qwen3:4b, read-only mount

# Verify + connect
nemoclaw factoryops status
nemoclaw factoryops connect
ls -la /sandbox/factoryops
exit

# UI
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8501
```

---

**One-sentence summary:** clone FactoryOps, paste `factoryops-kit` into
`load/`, start `ollama serve` pointed at `load/factoryops-kit/model-backup/ollama`,
run `nemoclaw onboard` for OpenClaw + OpenShell against that local model,
mount this repo read-only at `/sandbox/factoryops`, then test the
agent and run the UI — network off for the actual demo.
