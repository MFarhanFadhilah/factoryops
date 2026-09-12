# FactoryOps — NemoClaw-First Product and IT Requirements

**Version:** 2.1 — mandatory NemoClaw + Ollama/Qwen3 revision  
**Target:** Dell Pro Max with NVIDIA GB10  
**Build window:** 8 hours  
**Product:** Local, human-gated tablet-compression investigation agent  

## 1. Product decision

FactoryOps targets one synthetic rotary tablet press and four scenarios: abnormal compression force, tablet-weight variation, sticking/picking proxy, and excessive vibration indicating a possible tooling or bearing issue.

**NemoClaw is mandatory.** FactoryOps runs as an OpenClaw agent inside a NemoClaw-managed OpenShell sandbox. NemoClaw owns onboarding, lifecycle, policy application, and managed inference routing. The application remains decision support: it cannot write to a PLC, change process parameters, delete evidence, or disposition a batch.

## 2. Runtime architecture

```text
Dell Pro Max GB10 host
|-- NemoClaw CLI and versioned blueprint
|-- OpenShell gateway
|   |-- sandbox lifecycle and policy enforcement
|   |-- credentials/provider configuration
|   `-- inference.local -> host Ollama -> qwen3:8b
`-- NemoClaw-managed OpenShell sandbox: factoryops
    |-- OpenClaw runtime
    |   `-- FactoryOps Investigator
    |-- local typed read-only tools
    |-- local hybrid RAG and PDF/Markdown corpus
    |-- deterministic pharmaceutical policy gate
    |-- Streamlit interface
    `-- append-only demo audit log
```

OpenShell controls technical capabilities such as network, filesystem, process, and inference access. The FactoryOps policy engine independently controls domain actions such as inspection recommendations and batch-disposition denial.

## 3. Agent definition

> FactoryOps Investigator is a local OpenClaw agent deployed through NemoClaw that investigates tablet-press anomalies using telemetry, deterministic calculations, maintenance history, and cited GMP evidence, then submits a catalogued recommendation to a human approval gate.

### Behavioral contract

1. Treat typed tool output as authoritative numerical evidence.
2. Never invent thresholds, telemetry, citations, or maintenance records.
3. Retrieve evidence before recommending an action.
4. Separate observations, hypotheses, contradictory evidence, and missing evidence.
5. Never confirm sticking/picking from telemetry alone.
6. Select actions only from the approved action catalog.
7. Submit every proposed intervention to the deterministic policy gate.
8. Never write to equipment, change limits, or release/reject a batch.
9. Cite document title, page, and chunk.
10. Return `INSUFFICIENT_EVIDENCE` when support is inadequate.

### Loop limits

- Maximum 4 tool calls per investigation.
- Maximum 2 retrieval passes; the second occurs only if required evidence is missing.
- Maximum 1 JSON repair attempt.
- No recursive subagents, dynamic tools, autonomous prompt rewriting, or external web search.
- Temperature 0–0.2 and mandatory output-schema validation.

## 4. Ownership

| Owner | Final ownership | Required deliverable |
|---|---|---|
| Farhan | Telemetry, anomaly engine, deterministic calculations | Event replay, rule engine, risk score, maintenance and incident tools, typed JSON contracts |
| Ferdi | NemoClaw, OpenClaw agent, local RAG, orchestration | Host probe/onboarding, sandbox integration, agent skill, tool registration, hybrid retrieval, structured cited investigation |
| Gio | Policy gate, approval UX, product interface | Streamlit UI, action policy, `ALLOW/DENY/HUMAN_APPROVAL_REQUIRED`, approval modal, append-only audit display |
| Tika | Business, domain, and pitch | Persona, pain and ROI assumptions, intervention wording, demo storyline, slides, judge Q&A |

Farhan owns calculations. Ferdi owns evidence orchestration but not safety enforcement. Gio owns deterministic enforcement and human approval. Tika owns product framing, not root-cause determination.

## 5. Mandatory scope

1. Run `nemoclaw host probe` before onboarding.
2. Pull and warm `qwen3:8b` in host Ollama, then onboard an OpenClaw sandbox named `factoryops` with provider `ollama` and model `qwen3:8b`.
3. Verify that the OpenClaw agent reaches Ollama/Qwen3 8B through `inference.local`, not port 11434 directly.
4. Replay the supplied synthetic event stream.
5. Detect the four event types using deterministic rules.
6. Expose read-only telemetry, risk, maintenance, incident, and RAG tools to OpenClaw.
7. Generate a schema-valid investigation with citations and missing-evidence statements.
8. Apply the deterministic policy gate.
9. Require human approval for interventions and append the decision to the audit log.
10. Complete the core demo without cloud APIs.

### Out of scope

- GraphRAG, multi-planner/multi-executor orchestration, autoprompting, LLM fine-tuning, and hyperparameter sweeps.
- PLC/SCADA writes, direct stop commands, automatic rejection, electronic signatures, or production validation.
- Claims that synthetic thresholds or SOPs are appropriate for a real factory.

## 6. Functional requirements

### FR-1 NemoClaw readiness

The team shall capture the output of `nemoclaw host probe --json` and stop installation if a blocking result appears. The repository shall record the NemoClaw version, sandbox name, provider type, local model, and readiness status.

### FR-2 Onboarding and inference

The agent runtime shall be OpenClaw and the fixed inference stack shall be host Ollama with model tag `qwen3:8b`. NemoClaw shall configure the Ollama provider during onboarding, and the sandbox agent shall use `inference.local` rather than directly addressing Ollama on port 11434. The build shall pass `nemoclaw factoryops status` and `nemoclaw factoryops connect --probe-only` before application integration.

### FR-3 Synthetic telemetry

The application shall replay CSV records containing timestamp, machine and batch IDs, force values, estimated tablet weight, press and feeder speed, vibration, temperature, reject flag, scenario label, and demo risk score.

### FR-4 Deterministic analytics

Rule configuration shall be versioned outside prompts. Tools shall return rule ID, observed value, configured demonstration threshold, duration, severity, and calculation provenance.

### FR-5 Hybrid RAG

The local RAG service shall ingest PDFs and Markdown, preserve document/page/chunk/hash metadata, and combine lexical and dense retrieval. It shall retrieve top passages, optionally rerank locally, and provide explicit citations. Regulation, guidance, public machine manual, and synthetic SOP must remain distinguishable.

### FR-6 Investigation agent

Given one incident, the agent shall gather telemetry, calculations, maintenance records, and documents; produce 1–3 ranked hypotheses; show supporting, contradictory, and missing evidence; select one catalogued action; and request policy evaluation.

### FR-7 Policy and approval

The deterministic policy gate shall deny PLC writes, threshold changes, evidence deletion, definitive unsupported causes, and batch release/rejection. Inspection, sampling, tooling checks, and controlled-stop recommendations require human approval.

### FR-8 Audit trail

The system shall append incident ID, evidence IDs, retrieved citations, model/configuration identifiers, proposed action, policy result, approver, decision, rationale, and timestamp. Source telemetry must remain unchanged.

### FR-9 Offline demo

After installation and model/document preparation, the scripted product flow shall not require a cloud API. The UI shall display local-runtime, sandbox, inference-route, and network status.

## 7. Typed tools

```text
get_telemetry_window(incident_id, before_seconds, after_seconds)
evaluate_anomaly_rules(incident_id)
calculate_production_risk(incident_id)
get_maintenance_history(machine_id, component?)
search_rag_documents(query, document_types, top_k)
evaluate_policy(proposed_action, severity, evidence_complete, user_role)
append_audit_event(investigation, policy_decision, human_decision)
```

All tools must return JSON. Retrieval and telemetry tools are read-only. `append_audit_event` may only append under the demo audit directory.

## 8. Policy outcomes

| Proposed action | Required result |
|---|---|
| Continue monitoring | `ALLOW` or `HUMAN_APPROVAL_REQUIRED`, depending on severity |
| Hold and inspect | `HUMAN_APPROVAL_REQUIRED` |
| Hold and sample | `HUMAN_APPROVAL_REQUIRED` |
| Pause and inspect tooling | `HUMAN_APPROVAL_REQUIRED` |
| Recommend controlled stop | `HUMAN_APPROVAL_REQUIRED` |
| Write to PLC or change thresholds | `DENY` |
| Delete/alter evidence | `DENY` |
| Release or reject a batch | `DENY` |
| Confirm a root cause without sufficient evidence | `DENY` |

## 9. NemoClaw implementation

### Bootstrap

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

The fixed model is the text-only Ollama tag `qwen3:8b`. The package uses a 32,768-token operational context cap rather than the model's full advertised window to leave predictable room for the OpenClaw system prompt, tool schemas, retrieved evidence, and structured output. Do not expose Ollama directly to the sandbox or LAN; use NemoClaw's managed `inference.local` route.

### Runtime operations

```bash
nemoclaw factoryops status
nemoclaw factoryops logs --follow
nemoclaw factoryops connect
nemoclaw factoryops exec -- <command>
```

Use NemoClaw for sandbox creation, recreation, configuration, connection, and lifecycle management. Do not replace NemoClaw onboarding with hand-built OpenShell sandbox creation.

### Security requirements

- Deny external web search and messaging integrations.
- Permit only the managed `inference.local` route and required local application connections; deny direct sandbox access to Ollama port 11434.
- Keep credentials in the OpenShell provider mechanism, outside prompts and project files.
- Restrict writable application paths to project data, vector index, cache, and audit locations.
- Run all operational tools without privileged access.
- Expose no PLC, OPC-UA, or SCADA endpoint in the hackathon build.

### Qwen3 8B runtime constraints

- Use text input only; image classification remains a separate optional vision component.
- Keep the agent to one bounded plan and at most four typed tool calls.
- Request strict JSON matching `investigation.schema.json`; permit one repair retry.
- Keep retrieved evidence concise: normally top 4 final chunks after hybrid retrieval/reranking.
- Prefer deterministic tools for calculations and policy; Qwen3 8B synthesizes and explains evidence.
- If tool-call validation fails during onboarding, upgrade Ollama and rerun onboarding rather than parsing tool calls from plain text.

## 10. Data and vision

The included 2,700-row synthetic dataset is for event replay, integration, and evaluation—not LLM fine-tuning or real process-limit selection. Use deterministic rules first and optionally fit Isolation Forest only on normal contiguous windows.

Image data is not needed for the core demo. Force anomaly, weight variation, and vibration are telemetry scenarios. `sticking_picking_proxy` must remain a suspected condition requiring physical observation. Add binary normal/defect image upload only after the complete mandatory NemoClaw flow passes.

## 11. RAG corpus

The package includes current downloaded copies of 21 CFR Part 211, FDA process-validation/PAT/data-integrity/Part 11/OOS guidance, ICH Q8/Q9/Q10, one public rotary-press manual, and synthetic demo SOPs. Regulatory guidance is not a site SOP. Every synthetic SOP is labeled non-production.

Recommended chunking: 500–800 tokens with 80–120 overlap, page-aware extraction, top-8 hybrid retrieval, optional local reranking to top 4, and SHA-256 provenance checks.

## 12. Output schema

```json
{
  "incident_id": "INC-001",
  "machine_id": "PRESS-RTP41-DEMO",
  "batch_id": "BATCH-DEMO-001",
  "severity": "high",
  "observations": [{"metric": "main_compression_force_kn", "value": 23.1, "rule_id": "RULE-FORCE-01"}],
  "hypotheses": [{"name": "possible excess compression or fill variation", "confidence": "medium", "supporting_evidence": ["EV-1"], "contradictory_evidence": []}],
  "missing_evidence": ["physical tooling inspection"],
  "recommended_action": "HOLD_AND_INSPECT",
  "citations": [{"document": "SOP-DEMO-001", "page": null, "chunk": "c12"}],
  "policy_decision": "HUMAN_APPROVAL_REQUIRED"
}
```

## 13. Acceptance tests

1. `nemoclaw host probe` completes with no blocking readiness result, and the Ollama daemon/model pass local checks.
2. The `factoryops` OpenClaw sandbox is visible and healthy.
3. Status and doctor verify `qwen3:8b` on the Ollama-backed `inference.local` route used by the agent.
4. All four event windows trigger expected deterministic incident labels.
5. A normal window produces no critical recommendation.
6. Every investigation includes at least two evidence objects and one valid citation.
7. Missing documents produce `INSUFFICIENT_EVIDENCE`, never fabricated citations.
8. Batch release, PLC writes, threshold changes, and evidence deletion return `DENY`.
9. Interventions remain `HUMAN_APPROVAL_REQUIRED` until a user acts.
10. Approval appends a new audit event without changing source telemetry.
11. Invalid model JSON receives one repair attempt and then fails safely.
12. The complete scripted flow runs locally without a cloud API.

## 14. Eight-hour plan

| Time | Farhan | Ferdi | Gio | Tika |
|---|---|---|---|---|
| 0:00–0:45 | Freeze schemas/rules | Probe host; verify Ollama; pull/warm qwen3:8b; onboard NemoClaw/OpenClaw | Build Streamlit shell | Freeze vocabulary and story |
| 0:45–2:00 | Event replay and tool JSON | Verify inference, install agent skill, ingest corpus | Incident timeline and charts | Action catalog and business framing |
| 2:00–4:00 | Rules, risk, maintenance tools | Register tools, hybrid RAG, bounded agent loop | Policy gate and approval modal | Safe recommendation language and pitch |
| 4:00–5:30 | Integration fixes | Citations, schema, insufficiency path | Audit and NemoClaw status panel | Demo script and ROI assumptions |
| 5:30–6:45 | Acceptance testing | Acceptance testing | Acceptance testing | Judge Q&A |
| 6:45–8:00 | Freeze and rehearse | Freeze and rehearse | Freeze and rehearse | Two rehearsals and fallback recording |

If behind schedule, cut vision, reranking, and optional anomaly ML. **Do not cut NemoClaw**, deterministic policy, citations, or human approval.

## 15. Demo sequence

1. Show `nemoclaw factoryops status` and confirm the Ollama/Qwen3 8B `inference.local` route.
2. Open the application and display sandbox/local status.
3. Replay normal production, then inject abnormal force drift.
4. Show deterministic alert and production-at-risk calculation.
5. Ask the OpenClaw agent to investigate.
6. Show its telemetry, maintenance, SOP/manual evidence, citations, hypotheses, and missing physical inspection.
7. Show `HOLD_AND_INSPECT` routed to `HUMAN_APPROVAL_REQUIRED`.
8. Attempt batch release or PLC change and show `DENY`.
9. Approve inspection and show the appended audit event.

## 16. Definition of done

The project is complete only when the OpenClaw FactoryOps Investigator runs inside a healthy NemoClaw-managed OpenShell sandbox, uses the managed Ollama/Qwen3 8B route through `inference.local`, calls typed tools, retrieves local cited evidence, passes deterministic policy, requires human approval, and completes the scripted scenario without a cloud API.

## 17. Disclaimer

This is a synthetic hackathon demonstration, not a validated pharmaceutical manufacturing system. Its thresholds, SOPs, calculations, and recommendations must not be used to operate equipment or make GMP batch decisions.
