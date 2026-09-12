# FactoryOps

An offline maintenance-technician copilot that answers fault-code
questions from a plant's own manuals and repair history — **no cloud
calls, no internet, ever, during the live demo.**

## Stack (fixed by competition rules — do not substitute)

```text
GitHub → Dell GB10 host → local Ollama (chat + embedding) → NemoClaw → OpenShell sandbox → OpenClaw agent
```

| Component | Role |
|---|---|
| GitHub | Stores this repo: app code, data, manuals |
| Ollama | Runs the local chat + embedding models |
| `qwen3:4b` (🧪 test) / `qwen3:8b` (🏭 competition) | Answers FactoryOps questions |
| `nomic-embed-text` (🧪 test) / `mxbai-embed-large` (🏭 competition) | Embeds manuals/repair history for RAG retrieval |
| NemoClaw | Installer/manager for the agent + sandbox stack |
| OpenShell | Sandboxes the agent's file/network access |
| OpenClaw | The agent that runs inside the sandbox |
| FactoryOps (this repo) | Manuals, repair history, tools |

## Two ways to run this

| | 🧪 Test (your laptop) | 🏭 Competition (Dell GB10) |
|---|---|---|
| Goal | Validate the pipeline before the event | Actual event run |
| Model source | `load/factoryops-kit/model-backup/ollama/` — same as competition, never `ollama pull` | `load/factoryops-kit/model-backup/ollama/` only — **never** `ollama pull` |
| Network | On | On during setup, **off for the live demo** |

Steps are identical in both modes — Test just runs the same
`factoryops-kit` load on your laptop first, to confirm the copy is
good before you bring it to the event. Commands below run from the
repo root.

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
into `load/` → `load/factoryops-kit/`. Gitignored — re-paste on every fresh clone.

**🧪 Test (required too):** paste the same `factoryops-kit` into `load/`
on your laptop — Step 3 loads the model from it, same as the competition,
and this also lets you confirm the copy isn't corrupt before the event.

## 2. Check prerequisites

The Dell GB10 runs **DGX OS** (native Ubuntu, not WSL) with NVIDIA
driver/CUDA preinstalled. It normally lacks Docker-for-your-user,
Node/npm, Ollama, and NemoClaw — check and install those yourself.
Always check first; organizers may have customized the image.

```bash
nvidia-smi || echo "NO GPU — fine for laptop testing (CPU, slower); required on the Dell"
docker --version && docker info >/dev/null && echo "DOCKER READY" || echo "DOCKER MISSING"
node --version || echo "NODE MISSING"
npm --version || echo "NPM MISSING"
df -h ~
```
If missing, install:
```bash
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker "$USER" && newgrp docker
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs
```
Dell: `nvidia-smi` failing is unusual (driver ships preinstalled) —
don't reinstall/upgrade the driver yourself, ask a mentor. Don't
change NVIDIA driver/Docker/network policy without a mentor's OK.

## 3. Get the model

Check first:
```bash
command -v ollama >/dev/null 2>&1 && ollama --version || echo "OLLAMA NOT INSTALLED"
```
Install if missing:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Each environment serves **two** models — a chat model and an embedding
model (RAG retrieval over the manuals/repair history) — out of one
`OLLAMA_MODELS` directory. The kit ships each model in its own dir, so
merge the embedding model's `blobs/` + `manifests/` into the chat
model's dir once, per environment:

| | 🧪 Test (laptop) | 🏭 Competition (Dell GB10) |
|---|---|---|
| Chat model | `qwen3:4b` | `qwen3:8b` |
| Embedding model | `nomic-embed-text` | `mxbai-embed-large` |
| Merged into | `.../ollama/4b/` | `.../ollama/8b/` |

**🧪 Test (laptop) — load from the kit (same as competition, no `ollama pull`):**
```bash
sha256sum load/factoryops-kit/model-backup/llamafile/Qwen3.5-0.8B-Q8_0.llamafile
# expect: ec7c3ab7903accb1b4d890cfd1fc670fabc642dcb4896735bd69d46b2629408d
sudo systemctl stop ollama 2>/dev/null || true

# one-time: merge the embedding model into the chat model's dir
cp -n load/factoryops-kit/model-backup/ollama/embed-nomic-embed-text/blobs/* \
      load/factoryops-kit/model-backup/ollama/4b/blobs/
cp -rn load/factoryops-kit/model-backup/ollama/embed-nomic-embed-text/manifests/registry.ollama.ai/library/nomic-embed-text \
       load/factoryops-kit/model-backup/ollama/4b/manifests/registry.ollama.ai/library/

export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/4b"
ollama serve &
ollama list                                                        # expect qwen3:4b + nomic-embed-text
ollama run qwen3:4b "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl http://127.0.0.1:11434/api/embed -d '{"model":"nomic-embed-text","input":"test"}'
curl http://127.0.0.1:11434/api/tags
```
If `ollama list` errors, either model is missing, or the checksum
mismatches, the `factoryops-kit` copy is corrupt or incomplete —
re-copy it from the source before the competition.

**🏭 Competition (Dell GB10) — load from the kit, never pull:**
```bash
sudo systemctl stop ollama 2>/dev/null || true

# one-time: merge the embedding model into the chat model's dir
cp -n load/factoryops-kit/model-backup/ollama/embed-mxbai-embed-large/blobs/* \
      load/factoryops-kit/model-backup/ollama/8b/blobs/
cp -rn load/factoryops-kit/model-backup/ollama/embed-mxbai-embed-large/manifests/registry.ollama.ai/library/mxbai-embed-large \
       load/factoryops-kit/model-backup/ollama/8b/manifests/registry.ollama.ai/library/

export OLLAMA_MODELS="$(pwd)/load/factoryops-kit/model-backup/ollama/8b"
ollama serve &
ollama list                                                      # expect qwen3:8b + mxbai-embed-large
ollama run qwen3:8b "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl http://127.0.0.1:11434/api/embed -d '{"model":"mxbai-embed-large","input":"test"}'
curl http://127.0.0.1:11434/api/tags
```
> ⚠️ **Caution:** `ollama serve` is a background server, not a one-shot
> command — every later step (NemoClaw, OpenClaw, the Streamlit UI, and
> the live demo itself) talks to it at `127.0.0.1:11434`. Keep this
> shell/session open and don't kill this process from here through
> Step 8 and the demo. If it ever stops (closed terminal, reboot,
> `pkill ollama`), every downstream step will fail with a connection
> error until you run `ollama serve &` again.

**`qwen3:1.7b` (faster, less reliable):** the kit also ships `qwen3:1.7b`
in `.../ollama/1.7b/` — noticeably faster on CPU-only laptops, but see
the hallucination finding under **Troubleshooting** below: it fabricated
data and ignored grounding instructions on a normal/no-anomaly case.
Use it only for quick iteration on things like prompt wiring or the
Streamlit UI, never to judge whether an answer is actually correct.

### Quick model switch

Re-running the stop/merge/serve steps by hand every time you want to
try a different chat model gets old fast. Save this once, from the
repo root:

```bash
cat > switch-model.sh <<'SCRIPT'
#!/usr/bin/env bash
# Switch which chat+embedding pair is loaded from factoryops-kit.
# Usage: ./switch-model.sh [status | 1.7b | 4b | 8b]
#   status (or no argument) just reports what's currently loaded —
#   run this first if you're not sure what's active right now.
set -euo pipefail

MODEL="${1:-status}"

if [ "$MODEL" = "status" ]; then
  echo "== currently loaded (active ollama server) =="
  ollama list 2>/dev/null || echo "No ollama server reachable at \$OLLAMA_HOST (default 127.0.0.1:11434) — nothing is running"
  exit 0
fi

KIT="$(pwd)/load/factoryops-kit/model-backup/ollama"

case "$MODEL" in
  1.7b|4b) CHAT="qwen3:$MODEL"; EMBED="nomic-embed-text";   EMBED_DIR="embed-nomic-embed-text" ;;
  8b)      CHAT="qwen3:8b";     EMBED="mxbai-embed-large";  EMBED_DIR="embed-mxbai-embed-large" ;;
  *) echo "Unknown model '$MODEL' — expected status, 1.7b, 4b, or 8b" >&2; exit 1 ;;
esac

TARGET="$KIT/$MODEL"
[ -d "$TARGET" ] || { echo "Missing $TARGET — is factoryops-kit pasted into load/?" >&2; exit 1; }

echo "== stopping any running ollama server =="
sudo systemctl stop ollama 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
sleep 1

echo "== merging $EMBED into $MODEL (idempotent — skips files already there) =="
cp -n "$KIT/$EMBED_DIR/blobs/"* "$TARGET/blobs/"
mkdir -p "$TARGET/manifests/registry.ollama.ai/library"
cp -rn "$KIT/$EMBED_DIR/manifests/registry.ollama.ai/library/$EMBED" \
       "$TARGET/manifests/registry.ollama.ai/library/"

echo "== starting ollama serve against $TARGET =="
export OLLAMA_MODELS="$TARGET"
ollama serve > /tmp/ollama-switch.log 2>&1 &
sleep 2

echo "== verifying =="
ollama list
ollama run "$CHAT" "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl -s http://127.0.0.1:11434/api/embed -d "{\"model\":\"$EMBED\",\"input\":\"test\"}" | head -c 120
echo
echo "Active pair: $CHAT + $EMBED  (OLLAMA_MODELS=$TARGET)"
SCRIPT
chmod +x switch-model.sh
```

Check what's active before switching — don't assume:
```bash
./switch-model.sh status   # or just: ./switch-model.sh
```

Then switching is one line:
```bash
./switch-model.sh 4b     # test default
./switch-model.sh 1.7b   # faster, but known to hallucinate — quick iteration only, don't trust output
./switch-model.sh 8b     # competition pairing
```
`ollama serve` still runs as a plain background process here (not the
systemd service) — the same caution above applies: keep the shell open,
and re-run the script (or `ollama serve &`) if it ever dies.

**Fallback if Ollama can't run at all** (llamafile, portable, x86_64/ARM64):
```bash
LLAMAFILE="$(pwd)/load/factoryops-kit/model-backup/llamafile/Qwen3.5-0.8B-Q8_0.llamafile"
chmod +x "$LLAMAFILE" && "$LLAMAFILE" --server --nobrowser   # OpenAI-compatible API on :8080
```

## 4. Install NemoClaw

Check first, both modes:
```bash
command -v nemoclaw >/dev/null 2>&1 && nemoclaw --version || echo "NEMOCLAW NOT INSTALLED"
```

**Start clean, every time** — just in case (jaga-jaga): a stuck sandbox
registry entry from a prior attempt, even a failed one, breaks a fresh
install in confusing ways. Wipe before installing anything, even if
the check above said not installed:
```bash
docker rm -f $(docker ps -aq --filter name=factoryops) 2>/dev/null
rm -rf ~/.nemoclaw-portable-host.lock
command -v nemoclaw >/dev/null 2>&1 && nemoclaw uninstall --yes --destroy-user-data
docker system prune -a --volumes -f
```
Set the project folder *before* installing — note this is just a
shell variable for the command below, **not** something NemoClaw reads
automatically:
```bash
PROJECT_DIR="$(pwd -P)"
```
**🧪 Test on WSL2 + Docker Desktop only:** GPU passthrough reliably
fails there during onboarding (`Docker GPU patch failed`). CPU
inference is fine for testing, so disable it up front:
```bash
export NEMOCLAW_SANDBOX_GPU=0
```
**🏭 Competition:** leave GPU passthrough enabled, don't set that variable.

Install if missing:
```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```
Two prompts come up during install:
- License agreement → answer **y**
- `Run express install with these settings? [Y/n]` → answer **n** —
  express "balanced" opens npm/pypi/huggingface/brew access and web
  search, which conflicts with the Restricted policy below

Answering **n** drops straight into onboarding, which then runs
**automatically** — answer each prompt as it appears, in this order:
```text
Select agent runtime      → 1) OpenClaw
Select inference provider → 8) Local Ollama
Select model               → qwen3:4b (🧪 test) / qwen3:8b (🏭 competition)
Sandbox name                → factoryops
Apply configuration          → 1)
Web search                    → 1) No web search
Messaging channel              → none selected — skip
Resource profile                 → 4) Developer
Policy tier                       → Restricted (not the pre-highlighted Balanced)
Policy presets                      → keep only local-inference, uncheck the rest
```
Interrupted onboarding: `nemoclaw onboard --resume`. Unexpected sudo
prompt or wizard auto-starting on its own: Ctrl+C, check
`ps aux | grep nemoclaw` for a stray process before retrying.

> ⚠️ **This auto-chained wizard never mounts your project folder** —
> there is no prompt for it, and `PROJECT_DIR` is not read
> automatically. The only way to attach it is the `--host-mount` flag,
> which you pass by re-running onboarding explicitly right after,
> recreating the sandbox in place:
> ```bash
> nemoclaw onboard --name factoryops --recreate-sandbox \
>   --host-mount "$PROJECT_DIR:/sandbox/factoryops"
> ```
> This re-runs the same prompts above (still pick Restricted, etc.) but
> now actually binds your repo. Skipping this step is why `/sandbox`
> comes up empty in Step 5.

**🧪 WSL2:** if sandbox creation fails with `Docker GPU patch failed`
right after CUDA proof, you skipped the `NEMOCLAW_SANDBOX_GPU=0`
export above — go back, export it, redo onboarding. Don't retry the
same way.

Piped/automated input can auto-advance past the Policy tier/presets
screen before a keypress registers, landing on Balanced instead of
Restricted — see **Troubleshooting → Policy tier ended up Balanced**
below if that happens.

Once onboarding finishes:
```bash
source ~/.bashrc
nemoclaw --version
nemoclaw agents list      # OpenClaw should be listed
nemoclaw host probe
```

Expected settings:
```text
Agent runtime:          OpenClaw
Sandbox name:           factoryops
Inference provider:     Local Ollama
Model:                  qwen3:4b (🧪 test) / qwen3:8b (🏭 competition)
Project host folder:    $PROJECT_DIR
Sandbox project folder: /sandbox/factoryops
Project mount mode:     Read-only
Web search:             Disabled
Cloud inference:        Disabled
External API keys:      None
Network policy:         Local-only / deny Internet
```

## 5. Verify the sandbox and repo mount

```bash
nemoclaw factoryops status
nemoclaw factoryops connect
```
**If either fails:**
```bash
nemoclaw host probe             # host/sandbox health
docker ps -a                    # check for a crash-looping container
docker logs <container>         # see the actual failure
```
Then confirm `PROJECT_DIR="$(pwd -P)"` is absolute and re-run
`nemoclaw onboard` (or `--resume` if interrupted). If status shows
`Phase: Error` or the container keeps crash-looping, **don't**
repeatedly retry `nemoclaw <name> destroy` — a crash-looping container
never reaches a state NemoClaw can confirm absent, so `destroy` will
keep refusing with an identity-conflict error. Instead: `nemoclaw
uninstall`, then reinstall from Step 4.

Inside the sandbox — `pwd` right after connecting prints `/sandbox`
(the container's default working dir), but your project only shows up
under `/sandbox/factoryops` if onboarding was run with `--host-mount`
(see Step 4's warning above):
```bash
pwd && ls -la /sandbox/factoryops
head -n 5 /sandbox/factoryops/data/repair_history.csv
cat /sandbox/factoryops/manuals/lockout_tagout_sop.md
awk '$2 == "/sandbox/factoryops" { print $2, $4 }' /proc/mounts   # expect "ro"
exit
```
If `/sandbox/factoryops` doesn't exist but `/sandbox` itself does,
that's not a broken sandbox — it means onboarding ran without
`--host-mount`. See **Troubleshooting → `/sandbox/factoryops` missing**
below.

## 6. Test OpenClaw

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
Good answer: cites local files, applies the LOTO step before any
inspection instruction, invents nothing. Exit: `/exit`, then `exit`.

## 7. Build app/tools (once, before Step 8)

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

## 8. Run the UI

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8501
```
Open `http://localhost:8501`.

## 9. Editing during the event

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
- **Small model hallucinates facts not in the local files, especially on a "nothing abnormal" case** → observed with `qwen3:1.7b` during early testing (this is why the test default is `qwen3:4b`, not `1.7b`): asked to investigate a genuinely normal telemetry window, it invented a fake anomaly with units/thresholds that don't exist anywhere in the project (`"1200 psi vs. 1150-1250 psi"` — nothing in this project is measured in psi) and recommended stopping production. It ignored "use only local files" entirely and answered from generic training knowledge instead of reading the CSV. This is a real reliability gap, not a one-off:
  - Don't trust a model's prose claim by itself — cross-check against the deterministic tool output (e.g. `evaluate_anomaly_rules`/`calculate_production_risk` in `secret-folder/tools/`) before accepting a demo answer as correct.
  - Re-test every scenario (especially the normal/no-anomaly case) against the competition's actual `qwen3:8b` + `mxbai-embed-large` pairing before relying on `qwen3:4b` + `nomic-embed-text` results for the live demo. Smaller models are more prone to ignoring grounding instructions and inventing plausible-sounding but fabricated evidence — if you fall back to `1.7b` for quick iteration, re-verify anything it says before trusting it.
  - If it recurs on a larger model too, that's a prompt/skill-file problem (the "never invent facts absent from local files" rule needs to be stated more forcefully or earlier in context), not just a model-size problem.
- **Docker permission error** → `sudo usermod -aG docker "$USER" && newgrp docker`
- **`/sandbox/factoryops` missing (`/sandbox` exists but is otherwise empty)** → NemoClaw never mounts the project folder on its own — there's no wizard prompt for it, and setting `PROJECT_DIR` alone does nothing. The only way to attach your repo is the `--host-mount <host:/sandbox/path>` flag on `nemoclaw onboard` (confirmed via `nemoclaw onboard --help`), which the auto-chained wizard from the installer never passes. Fix in place, no NemoClaw reinstall needed:
  ```bash
  cd /path/to/factoryops               # repo root
  export NEMOCLAW_SANDBOX_GPU=0        # 🧪 WSL2 only — skip on the Dell
  PROJECT_DIR="$(pwd -P)"
  nemoclaw onboard --name factoryops --recreate-sandbox \
    --host-mount "$PROJECT_DIR:/sandbox/factoryops"
  ```
  `--recreate-sandbox` deletes and recreates the existing sandbox in
  place, so you don't need a separate `destroy` first. This re-runs the
  same wizard prompts as Step 4 (still pick Restricted, not Balanced) —
  verify after: `nemoclaw factoryops connect`, then `ls -la /sandbox/factoryops` should show your repo files.

  **If it errors instead** with something like *"The failed sandbox and container state is uncertain... Sandbox 'factoryops' was retained after registry publication failed... Do not delete the sandbox by mutable name"* followed by `Error: GPU sandbox local inference reachability failed for https://inference.local/v1/models` — that's a **different** sandbox from a previous WSL2 GPU-patch failure (see Step 4) stuck in a retained state that `--recreate-sandbox`/`destroy` refuses to touch. Don't keep retrying the same way. Do the **Full reset** below instead — `nemoclaw uninstall --yes --destroy-user-data` clears the retained-sandbox safety check that a plain destroy/recreate can't — then reinstall from Step 4 with `NEMOCLAW_SANDBOX_GPU=0` exported and use the `--host-mount` command above.
- **`nemoclaw uninstall` fails: "Failed to acquire lock"** → stale lock from a killed process:
  ```bash
  ps -p "$(cat ~/.nemoclaw-portable-host.lock/owner)"   # confirm dead before removing
  rm -rf ~/.nemoclaw-portable-host.lock
  nemoclaw uninstall
  ```
- **`nemoclaw uninstall` reports "gateway remove failed"** → usually harmless (already gone). Confirm: `openshell gateway list` should say "No gateways found." Otherwise `openshell gateway remove <name>` and retry.
- **Full reset** (when in doubt, tear down everything):
  ```bash
  docker rm -f $(docker ps -aq --filter name=factoryops) 2>/dev/null
  rm -rf ~/.nemoclaw-portable-host.lock
  nemoclaw uninstall --yes --destroy-user-data
  docker system prune -a --volumes -f
  docker images   # confirm empty
  ```
  Then reinstall from Step 4.
- **Policy tier ended up Balanced instead of Restricted** → the [8/8] Policy presets screen can auto-advance past your selection before a keypress registers, especially with piped/automated input. Check what's applied and trim it down rather than re-onboarding:
  ```bash
  nemoclaw factoryops policy list
  for p in brew huggingface npm pypi openclaw-pricing; do
    nemoclaw factoryops policy remove "$p" --yes
  done
  ```
  Keep `local-inference` (needed to reach Ollama). This only restricts the OpenClaw agent *inside* the sandbox — you still edit/`pip install` on the host (Step 9).
- **🧪 WSL2 sandbox creation disconnects** → check OOM: `dmesg -T | egrep -i 'oom|killed process'`. Raise WSL2 limits in `C:\Users\<you>\.wslconfig`:
  ```ini
  [wsl2]
  memory=12GB
  processors=6
  swap=8GB
  ```
  Then `wsl --shutdown` from PowerShell and reopen. Also raise Docker Desktop's resource limits if used.
- **🧪 WSL2 sandbox never reaches Ready / crash-loops (e.g. `libelf.so.1: file too short`) / `destroy` refuses to delete** → usually a corrupted image, not the GPU-patch issue above. Purge first:
  ```bash
  docker rm -f $(docker ps -aq --filter name=factoryops)
  docker system prune -a --volumes -f
  nemoclaw uninstall
  ```
  Still recurring (check `dmesg -T | egrep -i 'corrupt|i/o error'`)? The corruption is in Docker Desktop's backing VM disk — fix from Windows: `wsl --shutdown`, reopen Docker Desktop; if it recurs again, Docker Desktop → Troubleshoot → Clean/Purge data. Then reinstall from Step 4.
- **🏭 Any of the above on the Dell GB10** → these are known WSL2/Docker Desktop quirks and not expected on native Linux. Treat as a real anomaly and flag to a mentor rather than applying the WSL2 workaround.

## Final checklist

**🧪 Test (laptop)**
```text
[ ] factoryops-kit pasted into load/ on the laptop and its sha256 checksum matches
[ ] ollama serve against load/factoryops-kit/model-backup/ollama/4b answers the test prompt, ollama list shows qwen3:4b + nomic-embed-text (kit not corrupt)
[ ] NemoClaw sandbox onboarded and healthy
[ ] OpenClaw answers the M4-E17 scenario, citing local files + LOTO step
[ ] Streamlit UI runs at localhost:8501
```

**🏭 Competition (Dell GB10)**
```text
[ ] load/factoryops-kit/ pasted in
[ ] ollama serve runs against load/factoryops-kit/model-backup/ollama/8b, ollama list shows qwen3:8b + mxbai-embed-large
[ ] NemoClaw sandbox onboarded and healthy, /sandbox/factoryops mounted read-only
[ ] OpenClaw answers the M4-E17 scenario, citing local files + LOTO step
[ ] Streamlit UI runs at localhost:8501
[ ] No cloud inference, API key, or web search used anywhere
[ ] Full path re-tested with the network off
[ ] Code changes committed locally
```

---

**One-sentence summary:** clone FactoryOps, paste `factoryops-kit` into
`load/` and load `qwen3:4b` + `nomic-embed-text` from it on your
laptop to test, then do the same with `qwen3:8b` + `mxbai-embed-large`
on the Dell for the event — everything else (NemoClaw onboard,
sandbox verify, OpenClaw test, Streamlit UI) is identical in both
modes, with network cut only for the live demo.
