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

## 4. Install NemoClaw (both modes — command is identical, caveat differs)

**Start clean, every time.** Any prior attempt (even a failed one) can leave
a stuck sandbox registry entry that makes a fresh install fail in confusing
ways. Wipe first, before installing anything:
```bash
docker rm -f $(docker ps -aq --filter name=factoryops) 2>/dev/null
rm -rf ~/.nemoclaw-portable-host.lock
command -v nemoclaw >/dev/null 2>&1 && nemoclaw uninstall --yes --destroy-user-data
docker system prune -a --volumes -f
```

Set the project folder *before* installing — the installer chains straight
into the onboarding wizard below, so this must already be exported when it
asks for "Project host folder":
```bash
PROJECT_DIR="$(pwd -P)"
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
source ~/.bashrc
nemoclaw --version
nemoclaw agents list      # OpenClaw should be listed
nemoclaw host probe
```
Interrupted onboarding: `nemoclaw onboard --resume`. If install starts an
onboarding wizard on its own instead of just installing, or asks for a sudo
password unexpectedly, Ctrl+C and check `ps aux | grep nemoclaw` for a
stray process before retrying.

**🧪 Test (laptop, especially WSL2 + Docker Desktop): disable GPU passthrough
before installing.** Docker Desktop's WSL2 backend doesn't support NemoClaw's
native GPU passthrough — it falls back to a `--gpus` Docker-compatibility
patch, and that patch reliably fails during onboarding on this host type.
Symptom: onboarding gets through sandbox creation and CUDA proof, then dies
with `Docker GPU patch failed` / `Error: GPU sandbox local inference
reachability failed for https://inference.local/v1/models`, leaving a
retained sandbox stuck in `Provisioning`/`Error` phase that `nemoclaw
<name> destroy` will keep refusing to delete (it's a real, deterministic
failure, not flaky — retrying the same way won't help). This has nothing to
do with the model or DNS. Since CPU-only inference is already fine for
laptop testing (Step 2), just skip GPU passthrough entirely:
```bash
export NEMOCLAW_SANDBOX_GPU=0
```
run this in the same shell right before the `curl | bash` line above. Confirm
it took during onboarding's preflight: look for `✓ Sandbox GPU: disabled by
configuration` (not `enabled (auto)`). If you already hit the failure before
reading this, recover with the clean-start block above, then retry with the
variable exported. See **Troubleshooting → Docker GPU patch failed** below.

**🏭 Competition (Dell GB10):** DGX OS runs Docker natively on Linux (no
Docker Desktop compatibility layer), so this GPU-patch failure is not
expected — leave GPU passthrough enabled and don't set `NEMOCLAW_SANDBOX_GPU`.
Still run `nemoclaw host probe` after install to confirm. If you do see the
same `Docker GPU patch failed` error on the Dell, treat it as a real anomaly
worth flagging to a mentor rather than applying the WSL2 workaround.

If prompted `Run express install with these settings? [Y/n]`, answer **n** —
express mode's "balanced" tier enables npm/pypi/huggingface/brew access and a
web-search preset, which conflicts with the wizard answers in Step 5 (no web
search, local-only network). Answering `n` is expected and correct: it drops
you straight into the manual, prompt-by-prompt wizard from Step 5 — there is
no separate "just install, nothing else" path, so proceed directly into it.

## 5. Create the sandbox: NemoClaw + OpenShell + OpenClaw (both modes)

The wizard from Step 4 continues here automatically — you don't run a
separate command unless it didn't start (then run `nemoclaw onboard`
yourself; `$PROJECT_DIR` is already set from Step 4). Answer each prompt as
it appears, in order, starting with agent selection (`1) OpenClaw`):

**🧪 Test (laptop, WSL2):** this is the step where the Step 4 GPU-patch
issue actually surfaces if you skipped the `NEMOCLAW_SANDBOX_GPU=0` export —
sandbox creation can get all the way through CUDA proof, then fail with
`Docker GPU patch failed` and land in `Phase: Error`/`Provisioning` a few
seconds later. If that happens, don't retry the same way — go back to Step
4's clean-start block, export the variable, and redo onboarding.

At the **[8/8] Policy presets** step, pick **Restricted**, not the
pre-highlighted **Balanced** — Balanced opens real internet egress
(`npm`, `pypi`, `huggingface`, `brew` registries) that conflicts with the
project's local-only rule. If your input is piped (e.g. through an
automation/agent) the wizard can auto-advance past this screen on the
Balanced default before a keypress registers; if that happens, trim it down
afterwards instead of re-onboarding:
```bash
nemoclaw factoryops policy list                          # see what's applied
for p in brew huggingface npm pypi openclaw-pricing; do
  nemoclaw factoryops policy remove "$p" --yes
done
```
Keep `local-inference` — the sandbox needs it to reach your local Ollama.
This only restricts what the OpenClaw agent process *inside the sandbox*
can reach; it doesn't affect building the app itself (see Step 10 — you
edit and `pip install` on the host, not inside the sandbox).

**🏭 Competition (Dell GB10):** expect this step to complete cleanly in one
pass on native Linux. If you do see the same `Phase: Error` /
`inference.local` reachability failure here, treat it as a real anomaly
worth flagging to a mentor rather than the known WSL2 quirk.
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

If sandbox creation instead reports "reached Ready before OpenShell returned
one exact durable create identity" or the container keeps restarting, **stop**
— don't repeatedly retry `nemoclaw <name> destroy`. A crash-looping container
never reaches a state NemoClaw can confirm as absent, so destroy will keep
refusing with an "identity conflict" error and repeated attempts won't fix it.
Instead: `docker ps -a` to confirm the container is crash-looping, check
`docker logs <container>` for the actual failure (often the corrupted-image
issue in Step 4), then `nemoclaw uninstall` and reinstall from Step 4 rather
than hand-editing `~/.nemoclaw/*.json`.

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

Each entry is tagged for which mode it applies to: **both**, **🧪 test (WSL2/Docker Desktop)**, or **🏭 competition (Dell GB10, native Linux)**.

- **(both) Model missing / Ollama not running** → redo Step 3. Competition: re-copy `load/factoryops-kit/model-backup/ollama`. Never `ollama pull` as a workaround on the Dell.
- **(both) Docker permission error** → `sudo usermod -aG docker "$USER" && newgrp docker`
- **(both) NemoClaw onboarding interrupted** → `nemoclaw onboard --resume`
- **(both) Sandbox/OpenClaw unhealthy** → `nemoclaw factoryops status`, `nemoclaw host probe`. Don't delete the sandbox without a backup. If status shows `Phase: Error`, see **Docker GPU patch failed** below before assuming it's a model/config problem.
- **🧪 Docker GPU patch failed / `Error: GPU sandbox local inference reachability failed for https://inference.local/v1/models` / sandbox retained in `Provisioning` or `Error` phase and `destroy` refuses to delete it** → confirmed WSL2 + Docker Desktop limitation, not a model, DNS, or GPU-capability problem. Docker Desktop's WSL2 backend can't do NemoClaw's native GPU passthrough, only a `--gpus` compatibility patch, and that patch fails during onboarding on this host type. Everything downstream (the `inference.local` reachability check, the retained/unrecoverable sandbox) is a symptom of the GPU patch never finishing — the model and Ollama itself are fine. Fix: skip GPU passthrough entirely rather than trying to repair the patch:
  ```bash
  docker rm -f $(docker ps -aq --filter name=factoryops) 2>/dev/null
  rm -rf ~/.nemoclaw-portable-host.lock
  nemoclaw uninstall --yes --destroy-user-data   # the retained-sandbox safety check blocks a plain `destroy`; full uninstall clears it
  docker system prune -a --volumes -f
  export NEMOCLAW_SANDBOX_GPU=0                  # or rerun the installer with --no-gpu
  # then redo Step 4's install command
  ```
  Confirm during onboarding preflight: `✓ Sandbox GPU: disabled by configuration`. You may also see an unrelated-looking `host.openshell.internal has 2 distinct IPs` / `trusted-gateway SSRF exemption disabled` warning in `docker logs <container>` on the same failed attempt — that's a side effect of the same broken GPU patch path, not a separate bug. Not expected on the Dell GB10 (native Linux Docker, no compatibility-patch path) — if it happens there, flag it to a mentor instead of applying the WSL2 workaround.
- **(both) Repo not visible in sandbox** → confirm `PROJECT_DIR="$(pwd -P)"` is absolute, re-run `nemoclaw onboard`.
- **(both) NemoClaw state stuck / won't reinstall cleanly** → `nemoclaw uninstall`, then reinstall from Step 4.
- **(both) `nemoclaw uninstall` fails: "Failed to acquire lock on ~/.nemoclaw-portable-host.lock"** → the lock is stale, usually left by a NemoClaw process that was killed (e.g. `kill -9`) instead of exiting cleanly. Confirm the owning PID is actually dead, then remove the lock and retry:
  ```bash
  cat ~/.nemoclaw-portable-host.lock/owner        # PID it thinks holds the lock
  ps -p "$(cat ~/.nemoclaw-portable-host.lock/owner)"   # confirm dead/zombie before removing
  rm -rf ~/.nemoclaw-portable-host.lock
  nemoclaw uninstall
  ```
  Don't remove the lock if that PID is still a live NemoClaw process.
- **(both) `nemoclaw uninstall` reports "Uninstall completed with errors" / "Could not remove gateway registration 'nemoclaw': openshell gateway remove failed"** → usually harmless: the gateway was already removed by an earlier step, and `openshell gateway remove` errors on a gateway that no longer exists instead of treating it as success. Confirm there's nothing left before ignoring it:
  ```bash
  openshell gateway list        # "No gateways found." confirms it's already gone
  ```
  If it does list a gateway, remove it manually with `openshell gateway remove <name>` and re-run `nemoclaw uninstall`.
- **(both) Full reset: uninstall NemoClaw and remove everything** → when in doubt, tear down all of it in this order rather than picking individual fixes above:
  ```bash
  docker rm -f $(docker ps -aq --filter name=factoryops) 2>/dev/null   # stop any sandbox container
  rm -rf ~/.nemoclaw-portable-host.lock                                # clear a stale lock, if present
  nemoclaw uninstall --yes --destroy-user-data                         # remove CLI, OpenShell, ~/.nemoclaw state
  docker system prune -a --volumes -f                                  # purge all cached images/layers
  docker images                                                        # confirm empty
  command -v openshell >/dev/null 2>&1 && openshell gateway list || echo 'openshell removed (expected — uninstall removes it too)'
  ```
  Then reinstall fresh from Step 4. This is the same recovery path used
  above for a corrupted image or a stuck registry, just run end-to-end.
- **(both) Policy tier ended up `Balanced` instead of `Restricted`** → the wizard's Policy Presets screen (Step 5, [8/8]) can auto-advance past your selection before a keypress registers, especially with piped/automated input. Check what's applied and trim it down after the fact rather than re-onboarding:
  ```bash
  nemoclaw factoryops policy list
  for p in brew huggingface npm pypi openclaw-pricing; do
    nemoclaw factoryops policy remove "$p" --yes
  done
  ```
  Keep `local-inference` — it's what lets the sandbox reach your local Ollama. Removing the rest doesn't affect app development (Step 10: you build/edit on the host, not inside the sandbox).
- **🧪 Sandbox creation disconnects (laptop test on WSL2 only)** → check for OOM kills with `dmesg -T | egrep -i 'oom|killed process'`. WSL2 defaults to ~50% host RAM / no swap, which isn't enough for Docker + the sandbox + a loaded model at once. On Windows, create/edit `C:\Users\<you>\.wslconfig`:
  ```ini
  [wsl2]
  memory=12GB
  processors=6
  swap=8GB
  ```
  Then from PowerShell: `wsl --shutdown`, and reopen Ubuntu. If Docker Desktop's WSL2 backend is in use, also raise its memory/CPU limits under Settings → Resources.
- **(both, but the Windows-VM-disk fix below is 🧪 WSL2/Docker Desktop only) Sandbox never reaches Ready / container crash-loops (e.g. `libelf.so.1: file too short`) / `destroy` refuses with "could not select exactly one recovery record"** → a corrupted image, not a transient glitch; retrying `destroy` won't clear it since the crash-looping container never reaches a confirmable "absent" state. Note: `docker images` showing the same ID/age after reinstalling is *normal* (that timestamp is the image's build time, not your pull time) — it does **not** by itself mean Docker reused a bad local cache. Rule out a local cache issue first with a full purge:
  ```bash
  docker rm -f $(docker ps -aq --filter name=factoryops)   # stop the crash-looping container (frees the image)
  docker system prune -a --volumes -f                       # purge all cached images/layers, not just this one
  docker images                                              # confirm it's empty
  nemoclaw uninstall
  ```
  If the truncation still recurs after that (check `dmesg -T | egrep -i 'corrupt|i/o error'` for signs of an unclean WSL2/Docker Desktop VM shutdown), the corruption is in Docker Desktop's own backing VM disk, not Docker's image cache. Fix from **Windows**, not inside the distro:
  1. PowerShell: `wsl --shutdown`, then reopen Docker Desktop.
  2. If it recurs again, Docker Desktop → Troubleshoot → Clean/Purge data (or "Reset to factory defaults") to rebuild the VM disk — a plain restart alone doesn't repair existing corruption.
  Then reinstall from Step 4 and verify the freshly pulled image with
  `docker run --rm <image> ip netns list` before re-onboarding.

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
