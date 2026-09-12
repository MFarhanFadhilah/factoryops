# FactoryOps — NemoClaw + Ollama + Qwen3 8B

FactoryOps is a local OpenClaw investigation agent, running inside a NemoClaw-managed OpenShell sandbox, that investigates tablet-press anomalies from telemetry, deterministic calculations, maintenance history, and cited GMP evidence — then routes any recommendation through a human approval gate. The fixed inference stack is **host Ollama + `qwen3:8b`**, reached by the sandbox only through NemoClaw/OpenShell `inference.local`. It cannot write to a PLC, change process parameters, delete evidence, or disposition a batch.

License: MIT

## Contents

- [Repo map](#repo-map)
- [Setup](#setup)
- [Mandatory startup](#mandatory-startup)
- [Switching local models](#switching-local-models)
- [Typed tools](#typed-tools)
- [Policy gate](#policy-gate)
- [RAG corpus](#rag-corpus)
- [Running the demo](#running-the-demo)
- [Tests](#tests)
- [Audit trail](#audit-trail)
- [Full spec](#full-spec)

## Repo map

Core system — what actually runs:

| Path | Purpose |
|---|---|
| `agent/FACTORYOPS_SKILL.md` | The agent's behavioral contract (system prompt): mandatory rules, loop budget |
| `tools/registry.py` | Single entry point (`call_tool`) that OpenClaw's tool layer invokes; wires up all 8 tools below |
| `tools/*.py` | The 8 typed tools — telemetry, anomaly rules, risk, business impact, maintenance, RAG search, policy, audit |
| `tools/*_config.json`, `tools/blind_dataset_windows.json` | Versioned rule/business thresholds and blind-dataset window metadata, kept outside prompts |
| `schemas/tool_contracts.json` | Input/mode contract for every tool (`read_only` / `deterministic` / `append_only`) |
| `schemas/investigation.schema.json` | Required JSON output shape for an investigation |
| `policy/action_policy.json` | Deterministic `ALLOW` / `DENY` / `HUMAN_APPROVAL_REQUIRED` action catalog |
| `data/` | Synthetic tablet-press telemetry, maintenance history, incident catalog — see `data/DATASET_CARD.md` |
| `rag/` | Hybrid RAG corpus: `reference/` (FDA/ICH regulatory PDFs) + `demo-sops/` (synthetic SOPs), indexed via `rag/manifest.csv` |
| `docs/FactoryOps_PRD_NemoClaw.md` | Canonical product/IT requirements spec |
| `DEMO.md` | Copy-paste demo prompts for all 5 scenarios plus the guardrail and audit checks |
| `switch-model.sh` | Swaps which local Ollama chat+embedding pair is loaded |
| `requirements.txt` | Pinned external dependencies (`pypdf` for RAG PDF extraction; all other tools are stdlib) |
| `LICENSE` | MIT license (Team DoryClaw) |

Gitignored / local-only:

| Path | Purpose |
|---|---|
| `load/factoryops-kit/` | Local Ollama model backups, pasted in per machine — never `git pull`'d |
| `.venv/` | Python virtualenv (only external dependency: `pypdf`, for RAG PDF extraction) |
| `rag/_index_cache.json` | RAG index cache, rebuilt automatically whenever missing |

Pre-build background — not part of the running system, kept for reference:

| Path | Purpose |
|---|---|
| `factory-ops-brief.md` | Early market/positioning research for the original concept |
| `manuals/` | Fault-code manual + LOTO SOP from the earlier concept, superseded by `rag/` |
| `skills/` | The team's 8-file build methodology/checklist for the hackathon build window itself |

## Setup

```bash
git clone <this repo>
cd factoryops
python3 -m venv .venv && source .venv/bin/activate
pip install pypdf          # only external dependency; everything else is stdlib
```

Paste your `factoryops-kit` model backup into `load/` (gitignored, re-paste on every fresh clone) before switching models.

## Mandatory startup

```bash
nemoclaw host probe --json
ollama --version
ollama pull qwen3:8b
ollama run qwen3:8b "Reply only READY"

NEMOCLAW_AGENT=openclaw \
NEMOCLAW_PROVIDER=ollama \
NEMOCLAW_MODEL=qwen3:8b \
NEMOCLAW_SANDBOX_NAME=factoryops \
NEMOCLAW_CONTEXT_WINDOW=32768 \
NEMOCLAW_REASONING=true \
NEMOCLAW_INFERENCE_INPUTS=text \
nemoclaw onboard --non-interactive --yes --yes-i-accept-third-party-software

nemoclaw factoryops status
nemoclaw factoryops connect --probe-only
nemoclaw factoryops doctor --json
```

Do not bypass NemoClaw, expose Ollama to the LAN, or let the sandbox call port 11434 directly — the agent must only reach inference through `inference.local`.

## Switching local models

```bash
./switch-model.sh status   # what's actually loaded right now (default if no arg)
./switch-model.sh 8b       # qwen3:8b + mxbai-embed-large — competition pair
./switch-model.sh 4b       # qwen3:4b + nomic-embed-text — lighter test pair
./switch-model.sh 1.7b     # qwen3:1.7b + nomic-embed-text — fastest test pair
```

Requires the matching model already present under `load/factoryops-kit/model-backup/ollama/`.

## Typed tools

All calls go through `tools/registry.py:call_tool(name, **kwargs)`, which enforces the mode declared below. `read_only`/`deterministic` tools never write to disk; `append_audit_event` only ever appends.

| Tool | Mode | What it does |
|---|---|---|
| `get_telemetry_window` | read_only | Raw telemetry rows around an incident's real event window (scanned, not guessed) |
| `evaluate_anomaly_rules` | read_only | Deterministic threshold rules over a telemetry window |
| `calculate_production_risk` | read_only | Production risk score for an incident |
| `calculate_business_impact` | deterministic | Tablets/dollars at risk if unaddressed |
| `get_maintenance_history` | read_only | Work orders for a machine, optionally filtered by component |
| `search_rag_documents` | read_only | Lexical TF-IDF retrieval over the RAG corpus, with citations |
| `evaluate_policy` | deterministic | The enforcement gate — never model-decided |
| `append_audit_event` | append_only | Appends one event to the audit log; never rewrites or deletes |

## Policy gate

`policy/action_policy.json` is the single source of truth; `tools/policy.py` just applies it.

| Proposed action | Result |
|---|---|
| `CONTINUE_MONITORING` | `ALLOW` (or `HUMAN_APPROVAL_REQUIRED` if evidence incomplete/severity high) |
| `HOLD_AND_INSPECT`, `HOLD_AND_SAMPLE`, `PAUSE_AND_INSPECT_TOOLING`, `CONTROLLED_STOP_AND_MAINTENANCE_REVIEW` | `HUMAN_APPROVAL_REQUIRED` |
| `WRITE_PLC`, `CHANGE_THRESHOLD`, `DELETE_EVIDENCE`, `RELEASE_BATCH`, `REJECT_BATCH`, `CONFIRM_UNSUPPORTED_ROOT_CAUSE` | `DENY` — never overridable |
| Anything else | `DENY` (default) |

## RAG corpus

`rag/manifest.csv` lists every source document with a SHA-256 hash, checked at index time so retrieval never serves silently-altered content. Two classifications, kept distinguishable in every result:

- `regulation/guidance/manual` — `rag/reference/`: 21 CFR Part 211, FDA data-integrity/OOS/PAT/Part 11/process-validation guidance, ICH Q8/Q9/Q10, one public rotary-press manual
- `synthetic non-production SOP` — `rag/demo-sops/`: 5 demo SOPs, explicitly non-production

Run `python3 tools/rag_search.py` to (re)build `rag/_index_cache.json` and sanity-check search.

## Running the demo

See `DEMO.md` for 9 ready-to-paste prompts: normal operation, all 4 incident types, a guardrail-refusal check, and a human-approval + audit-trail check.

## Tests

All unit and contract tests can be executed with:

```bash
pytest tests/ -v
```

| Test file | What it tests |
|---|---|
| `tests/test_tools_readonly.py` | Read-only tools against baseline and incident telemetry/history (`INC-000` to `INC-004`) |
| `tests/test_policy.py` | Action policy gate enforcement (`ALLOW`, `DENY`, `HUMAN_APPROVAL_REQUIRED`) |
| `tests/test_registry.py` | Tool registry contract adherence, unknown tool handling, and execution modes |

## Audit trail

`tools/audit.py` appends every investigation + policy decision + human decision to `data/audit_log.jsonl` (created on first write, append-only). Inspect it with:

```bash
python3 -c "from tools.audit import read_audit_log; import json; print(json.dumps(read_audit_log(), indent=2))"
```

## Full spec

`docs/FactoryOps_PRD_NemoClaw.md` is the canonical requirements document — architecture, functional requirements, acceptance tests, and the build plan. This README is the map; that file is the contract.

---

Synthetic hackathon demonstration only — not a validated pharmaceutical manufacturing system. Its thresholds, SOPs, and recommendations must not be used to operate real equipment or make real GMP batch decisions. License: MIT.
