"""
Deterministic post-hoc check for agent responses. Model instructions alone
are not reliable — this catches the fabrication patterns actually observed
in practice, independent of which model produced the text:

  - a cited SOP/manual filename that doesn't exist under rag/
  - a cited work_order ID not present in maintenance_history.csv
  - a cited incident ID not present in incidents.jsonl
  - a telemetry unit/field that isn't in the real schema (e.g. "psi")
  - a "section N" / "§N" citation against action_policy.json, which has
    no numbered sections
  - a proposed action ID not in action_policy.json's catalogs

Read-only: never edits the response, only reports. Not a substitute for
`evaluate_policy` — this checks whether claims are *real*, not whether an
action is *allowed*.
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import ACTION_POLICY_JSON, INCIDENTS_JSONL, MAINTENANCE_CSV, RAG_DIR

KNOWN_TELEMETRY_FIELDS = {
    "main_compression_force_kn", "precompression_force_kn", "ejection_force_kn",
    "tablet_weight_mg", "turret_speed_rpm", "feeder_speed_rpm", "vibration_rms_mm_s",
    "bearing_temp_c", "reject_flag", "tablet_hardness_kp", "tablet_thickness_mm",
    "scenario_label", "production_risk_score",
}
FORBIDDEN_UNITS = ("psi", "bar", "fahrenheit", "°f")


def _real_documents():
    return {p.name for p in RAG_DIR.rglob("*") if p.is_file()}


def _real_work_orders():
    with open(MAINTENANCE_CSV) as f:
        return {row["work_order"] for row in csv.DictReader(f)}


def _real_incident_ids():
    ids = set()
    with open(INCIDENTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                ids.add(json.loads(line)["incident_id"])
    return ids


def _policy_action_ids():
    with open(ACTION_POLICY_JSON) as f:
        policy = json.load(f)
    return set(policy["always_deny"]) | set(policy["human_required"]) | set(policy["conditionally_allow"])


def validate(text):
    """Returns a list of finding dicts; empty list means nothing flagged."""
    findings = []

    real_docs = _real_documents()
    for m in re.finditer(r"[\w\- ]+?\.(?:md|pdf)\b", text):
        name = m.group(0).strip()
        # only check the bare filename, not surrounding prose picked up by the regex
        candidates = [name, name.split()[-1]] if " " in name else [name]
        if not any(c in real_docs for c in candidates):
            findings.append({
                "type": "unknown_document",
                "text": name,
                "detail": "not found anywhere under rag/ — likely fabricated citation",
            })

    real_wos = _real_work_orders()
    for m in re.finditer(r"\bWO-\d{4,}\b", text):
        if m.group(0) not in real_wos:
            findings.append({
                "type": "unknown_work_order",
                "text": m.group(0),
                "detail": "not present in maintenance_history.csv",
            })

    real_incidents = _real_incident_ids()
    for m in re.finditer(r"\bINC-\d{3,}\b", text):
        if m.group(0) not in real_incidents:
            findings.append({
                "type": "unknown_incident_id",
                "text": m.group(0),
                "detail": "not present in incidents.jsonl",
            })

    for unit in FORBIDDEN_UNITS:
        if re.search(rf"\b\d+(\.\d+)?\s*{re.escape(unit)}\b", text, re.IGNORECASE):
            findings.append({
                "type": "invalid_unit",
                "text": unit,
                "detail": "not a unit used by any field in tablet_press_events.csv",
            })

    for m in re.finditer(r"(?:§|[Ss]ection)\s*\d+(\.\d+)*", text):
        if "action_policy" in text.lower() or "policy" in text.lower():
            findings.append({
                "type": "invalid_policy_citation",
                "text": m.group(0),
                "detail": "action_policy.json has no numbered sections",
            })

    known_actions = _policy_action_ids()
    for m in re.finditer(r"\b[A-Z][A-Z_]{4,}\b", text):
        token = m.group(0)
        if token in ("INSUFFICIENT_EVIDENCE",):
            continue
        looks_like_action = token.endswith(("_PLC", "_BATCH", "_MONITORING", "_INSPECT", "_SAMPLE",
                                              "_TOOLING", "_REVIEW", "_THRESHOLD", "_EVIDENCE", "_ROOT_CAUSE"))
        if looks_like_action and token not in known_actions:
            findings.append({
                "type": "unknown_action_id",
                "text": token,
                "detail": "not one of the action IDs in action_policy.json",
            })

    return findings


if __name__ == "__main__":
    text = sys.stdin.read() if not sys.argv[1:] else Path(sys.argv[1]).read_text()
    findings = validate(text)
    if not findings:
        print("No fabrication patterns detected.")
    else:
        print(f"{len(findings)} finding(s):")
        for f in findings:
            print(f"  [{f['type']}] {f['text']!r} — {f['detail']}")
    sys.exit(1 if findings else 0)
