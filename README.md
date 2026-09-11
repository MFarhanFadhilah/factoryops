# FactoryOps

An offline maintenance-technician copilot that answers fault-code
questions from a plant's own manuals and repair history — **no cloud
calls, no internet, ever, during the live demo.**

## Stack (fixed by competition rules — do not substitute)

```text
GitHub → Dell GB10 host → local Ollama (qwen3:4b) → NemoClaw → OpenShell sandbox → OpenClaw agent
```

| Component | Role |
|---|---|
| GitHub | Stores this repo: app code, data, manuals |
| Ollama | Runs the local LLM |
| qwen3:4b | Answers FactoryOps questions |
| NemoClaw | Installer/manager for the agent + sandbox stack |
| OpenShell | Sandboxes the agent's file/network access |
| OpenClaw | The agent that runs inside the sandbox |
| FactoryOps (this repo) | Manuals, repair history, tools |

## Two ways to run this

| | 🧪 Test (your laptop) | 🏭 Competition (Dell GB10) |
|---|---|---|
| Goal | Validate the whole pipeline before the event | Actual event run |
| Model source | `ollama pull qwen3:4b` — internet OK | `load/factoryops-kit/model-backup/ollama/` only — **never** `ollama pull` |
| Network | On | On during setup, **off for the live demo** |

Everything else (NemoClaw, sandbox, OpenClaw, UI, test prompts) is
identical in both modes — only **Steps 2–3** (prerequisites, getting
the model) differ. Test mode also lets you mount `factoryops-kit` on
your laptop first, to confirm the copy you're carrying to the
competition isn't corrupt. Commands below are run from the repo root.

## Repo structure

```text
factoryops/
├── app/, tools/        empty skeletons — see "Build app/tools" below
├── data/repair_history.csv
├── manuals/fault_code_catalog.md, lockout_tagout_sop.md
├── load/factoryops-kit/  gitignored — competition-mode model + demo script
└── skills/skills/        process/agent-design notes
```

---

## 1. Clone

```bash
git clone https://github.com/MFarhanFadhilah/factoryops.git
cd factoryops
```

**🏭 Competition (required):** copy `factoryops-kit` from your flashdisk
into `load/` (paste, no command needed) → `load/factoryops-kit/`.
Gitignored, so re-paste it on every fresh clone.

**🧪 Test (optional but recommended):** paste the same `factoryops-kit`
into `load/` on your laptop too, so Step 3 can verify it isn't corrupt
before you bring it to the event.

## 2. Check prerequisites

### Is the Dell GB10 plain Linux?

Yes. Dell Pro Max with GB10 is an NVIDIA GB10 (Grace Blackwell) system
running **DGX OS** — a native Ubuntu-based Linux, not WSL. Out of the
box it already has: NVIDIA driver + CUDA, and the NVIDIA AI stack
(NemoClaw installs cleanly on top of it). It normally does **not**
already have: Docker set up for your user, Node.js/npm, Ollama, or
NemoClaw itself — install/verify those yourself below. Always run the
checks first since organizers may have customized the image.

**🧪 Test (laptop):**
```bash
docker --version && docker info >/dev/null && echo "DOCKER READY" || echo "DOCKER MISSING"
node --version || echo "NODE MISSING"
npm --version || echo "NPM MISSING"
nvidia-smi || echo "NO GPU — ollama will run on CPU (slower, fine for testing)"
df -h ~
```
If missing, install:
```bash
# Docker
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker "$USER" && newgrp docker
# Node.js/npm (LTS)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs
```
No GPU on your laptop is fine for testing — it just runs slower. Have
a GPU? `nvidia-smi` should list it, and Ollama uses it automatically
for faster inference — no extra config needed.

**🏭 Dell GB10:**
```bash
nvidia-smi
docker --version && docker info >/dev/null && echo "DOCKER READY" || echo "DOCKER MISSING"
node --version || echo "NODE MISSING"
npm --version || echo "NPM MISSING"
df -h ~
```
If missing, install:
```bash
# Docker
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker "$USER" && newgrp docker
# Node.js/npm (LTS)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs
```
`nvidia-smi` failing on the Dell is unusual (driver ships preinstalled)
— don't try to reinstall/upgrade the driver yourself, ask a mentor first.
Don't change NVIDIA driver/Docker/network policy without a mentor's OK.

## 3. Get the model

**🧪 Test (laptop) — normal pull:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen3:4b
ollama run qwen3:4b "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl http://127.0.0.1:11434/api/tags
```

**🧪 Test (laptop) — verify `factoryops-kit` isn't corrupt (recommended before the event):**
Paste `factoryops-kit` into `load/` on your laptop too (same as Step 1's
competition instruction), then point Ollama at it exactly like the Dell
will, to prove the copy is good before you travel with it:
```bash
sha256sum load/factoryops-kit/model-backup/llamafile/Qwen3.5-0.8B-Q8_0.llamafile
# expect: ec7c3ab7903accb1b4d890cfd1fc670fabc642dcb4896735bd69d46b2629408d
sudo systemctl stop ollama 2>/dev/null || true
export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/4b"
ollama serve &
ollama list                                                      # should list qwen3:4b, no errors
ollama run qwen3:4b "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl http://127.0.0.1:11434/api/tags
```
If any of these fail or hang (missing manifest, checksum mismatch,
`ollama list` errors), the kit copy is corrupt or incomplete — re-copy
`factoryops-kit` from the source before the competition.

**🏭 Competition (Dell GB10):**
```bash
curl -fsSL https://ollama.com/install.sh | sh   # only if not already installed
sudo systemctl stop ollama 2>/dev/null || true
export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/4b"
ollama serve &
ollama list
ollama run qwen3:4b "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl http://127.0.0.1:11434/api/tags
```
Never run `ollama pull` on the Dell. Leave `ollama serve` running for
the rest of setup.

8B backup: stop the server, `export OLLAMA_MODELS=".../ollama/8b"`,
`ollama serve` again, then `ollama run qwen3:8b` (copy `blobs/` +
`manifests/` into `.../ollama/8b/` first — kit ships the 4B only).

Fallback if Ollama can't run at all (llamafile, portable — runs on
x86_64 and ARM64 unmodified):
```bash
LLAMAFILE="$(pwd)/load/factoryops-kit/model-backup/llamafile/Qwen3.5-0.8B-Q8_0.llamafile"
sha256sum "$LLAMAFILE"   # ec7c3ab7903accb1b4d890cfd1fc670fabc642dcb4896735bd69d46b2629408d
chmod +x "$LLAMAFILE" && "$LLAMAFILE" --server --nobrowser   # OpenAI-compatible API on :8080
```

## 4. Install NemoClaw (both modes)

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
source ~/.bashrc
nemoclaw --version
nemoclaw agents list      # OpenClaw should be listed
nemoclaw host probe
```
Interrupted onboarding: `nemoclaw onboard --resume`.

## 5. Create the sandbox: NemoClaw + OpenShell + OpenClaw (both modes)

```bash
PROJECT_DIR="$(pwd -P)"
nemoclaw onboard
```
Wizard answers (same for both modes):
```text
Agent runtime:          OpenClaw
Sandbox name:           factoryops
Inference provider:     Local Ollama
Model:                  qwen3:4b
Project host folder:    $PROJECT_DIR
Sandbox project folder: /sandbox/factoryops
Project mount mode:     Read-only
Web search:             Disabled
Cloud inference:        Disabled
External API keys:      None
Network policy:         Local-only / deny Internet
```

## 6. Verify the sandbox and repo mount (both modes)

```bash
nemoclaw factoryops status
nemoclaw factoryops connect
```
Inside the sandbox:
```bash
pwd && ls -la /sandbox/factoryops
head -n 5 /sandbox/factoryops/data/repair_history.csv
cat /sandbox/factoryops/manuals/lockout_tagout_sop.md
awk '$2 == "/sandbox/factoryops" { print $2, $4 }' /proc/mounts   # expect "ro"
exit
```
Not visible? Confirm `PROJECT_DIR="$(pwd -P)"` is absolute, re-run `nemoclaw onboard`.

## 7. Test OpenClaw (both modes)

```bash
nemoclaw factoryops connect
openclaw tui
```
Sanity check: `Reply exactly: FACTORYOPS OPENCLAW READY.`

Project-read check: `Read /sandbox/factoryops/README.md. Reply in
exactly one sentence describing this project. Do not use web search or
any external network.`

FactoryOps scenario (full choreography in
`load/factoryops-kit/demo/demo-script.md`):
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
A good answer cites the local files, applies the LOTO step before any
inspection instruction, and invents nothing. Exit: `/exit`, then `exit`.

## 8. Build app/tools (once, before Step 9)

`app/` and `tools/` ship empty. Create:
```text
app/main.py         Streamlit UI
app/local_llm.py    client for http://127.0.0.1:11434
app/retrieval.py    search data/repair_history.csv + manuals/*.md
tools/search_manuals.py, get_repair_history.py, safety_gate.py
```
```bash
touch app/main.py app/local_llm.py app/retrieval.py \
      tools/search_manuals.py tools/get_repair_history.py tools/safety_gate.py
rm -f app/.gitkeep tools/.gitkeep
```

## 9. Run the UI (both modes)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8501
```
Open `http://localhost:8501`.

## 10. Editing during the event (both modes)

Edit on the **host**, not inside the read-only sandbox mount:
```bash
nano app/main.py
nemoclaw factoryops connect && head -n 30 /sandbox/factoryops/app/main.py && exit
git add -A && git commit -m "Hackathon demo checkpoint"
```
Push only if network access and rules allow it.

---

## Troubleshooting

- **Model missing / Ollama not running** → redo Step 3. Competition: re-copy `load/factoryops-kit/model-backup/ollama`. Never `ollama pull` as a workaround on the Dell.
- **Docker permission error** → `sudo usermod -aG docker "$USER" && newgrp docker`
- **NemoClaw onboarding interrupted** → `nemoclaw onboard --resume`
- **Sandbox/OpenClaw unhealthy** → `nemoclaw factoryops status`, `nemoclaw host probe`. Don't delete the sandbox without a backup.
- **Repo not visible in sandbox** → confirm `PROJECT_DIR="$(pwd -P)"` is absolute, re-run `nemoclaw onboard`.

## Final checklist

**🧪 Test (laptop)**
```text
[ ] ollama pull qwen3:4b works, model answers the test prompt
[ ] factoryops-kit pasted into load/ on the laptop and its sha256 checksum matches
[ ] ollama serve against load/factoryops-kit/model-backup/ollama/4b also answers the test prompt (kit not corrupt)
[ ] NemoClaw sandbox onboarded and healthy
[ ] OpenClaw answers the M4-E17 scenario, citing local files + LOTO step
[ ] Streamlit UI runs at localhost:8501
```

**🏭 Competition (Dell GB10)**
```text
[ ] load/factoryops-kit/ pasted in
[ ] ollama serve runs against load/factoryops-kit/model-backup/ollama, ollama list shows qwen3:4b
[ ] NemoClaw sandbox onboarded and healthy, /sandbox/factoryops mounted read-only
[ ] OpenClaw answers the M4-E17 scenario, citing local files + LOTO step
[ ] Streamlit UI runs at localhost:8501
[ ] No cloud inference, API key, or web search used anywhere
[ ] Full path re-tested with the network off
[ ] Code changes committed locally
```

## Cheat sheet

**🧪 Test:**
```bash
git clone https://github.com/MFarhanFadhilah/factoryops.git && cd factoryops
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen3:4b
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash && source ~/.bashrc
PROJECT_DIR="$(pwd -P)"; nemoclaw onboard
nemoclaw factoryops status
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8501
```

**🏭 Competition:**
```bash
git clone https://github.com/MFarhanFadhilah/factoryops.git && cd factoryops
# paste factoryops-kit into load/
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl stop ollama 2>/dev/null || true
export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/4b"
ollama serve &
ollama run qwen3:4b "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash && source ~/.bashrc
PROJECT_DIR="$(pwd -P)"; nemoclaw onboard
nemoclaw factoryops status
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8501
# cut network before the live demo
```

---

**One-sentence summary:** clone FactoryOps, test on your laptop with
`ollama pull qwen3:4b`, then for the event paste `factoryops-kit` into
`load/` and load the model from there instead — everything else
(NemoClaw onboard, sandbox verify, OpenClaw test, Streamlit UI) is the
same in both modes, with network cut only for the live demo.
