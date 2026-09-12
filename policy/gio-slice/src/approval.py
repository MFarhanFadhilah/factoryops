from datetime import datetime, timezone

from policy_gate import ROLE_QA, ROLE_SUPERVISOR, signatures_satisfy

STATE_PRESENTED = "Presented"
STATE_SUPERVISOR_SIGNED = "SupervisorSigned"
STATE_BOTH_SIGNED = "BothSigned"
STATE_RESOLVED = "Resolved"

MEANING_SUPERVISOR = "intervention approved"
MEANING_QA = "batch disposition reviewed"

SIGNER_SUPERVISOR_NAME = "A. Rivera"
SIGNER_QA_NAME = "K. Chen"

AUDIT_FIELDS = ("who", "what", "when", "why", "before")


def _now(clock):
    if clock is not None:
        return clock
    return datetime.now(timezone.utc)


def _iso(clock):
    stamp = _now(clock)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.isoformat()


def new_record(incident, option, gate):
    return {
        "state": STATE_PRESENTED,
        "incident_id": incident["incident_id"],
        "option_id": option["id"],
        "option_description": option.get("description"),
        "change_type": gate.get("change_type"),
        "decision": gate["decision"],
        "required_approvers": list(gate["required_approvers"]),
        "regulatory_basis": list(gate.get("regulatory_basis") or []),
        "signatures": [],
        "audit": [],
        "data_source": incident.get("data_source", "simulated"),
        "quality_flag": gate["quality_flag"],
    }


def append_audit(record, who, what, why, before, clock=None):
    entry = {
        "who": who,
        "what": what,
        "when": _iso(clock),
        "why": why,
        "before": before,
        "data_source": record.get("data_source", "simulated"),
    }
    record["audit"].append(entry)
    return entry


def _has_role(record, role):
    return any(sig.get("role") == role for sig in record["signatures"])


def _advance_if_complete(record):
    if signatures_satisfy(record["required_approvers"], record["signatures"]):
        record["state"] = STATE_BOTH_SIGNED
    elif _has_role(record, ROLE_SUPERVISOR):
        record["state"] = STATE_SUPERVISOR_SIGNED
    else:
        record["state"] = STATE_PRESENTED


def sign_supervisor(record, name=SIGNER_SUPERVISOR_NAME, clock=None):
    if record["state"] != STATE_PRESENTED:
        return record
    if ROLE_SUPERVISOR not in record["required_approvers"]:
        return record
    if _has_role(record, ROLE_SUPERVISOR):
        return record
    before = {"state": record["state"], "signatures": [sig["role"] for sig in record["signatures"]]}
    timestamp = _iso(clock)
    record["signatures"].append(
        {
            "role": ROLE_SUPERVISOR,
            "name": name,
            "meaning": MEANING_SUPERVISOR,
            "timestamp": timestamp,
        }
    )
    append_audit(
        record,
        who=name,
        what=f"signed option {record['option_id']} on {record['incident_id']}",
        why=f"{record['change_type']}: {MEANING_SUPERVISOR}",
        before=before,
        clock=clock,
    )
    _advance_if_complete(record)
    return record


def sign_qa(record, name=SIGNER_QA_NAME, clock=None):
    if record["state"] != STATE_SUPERVISOR_SIGNED:
        return record
    if ROLE_QA not in record["required_approvers"]:
        return record
    if _has_role(record, ROLE_QA):
        return record
    before = {"state": record["state"], "signatures": [sig["role"] for sig in record["signatures"]]}
    timestamp = _iso(clock)
    record["signatures"].append(
        {
            "role": ROLE_QA,
            "name": name,
            "meaning": MEANING_QA,
            "timestamp": timestamp,
        }
    )
    append_audit(
        record,
        who=name,
        what=f"reviewed batch disposition for {record['incident_id']}",
        why="21 CFR 211.22",
        before=before,
        clock=clock,
    )
    _advance_if_complete(record)
    return record


def resolve(record, clock=None):
    if record["state"] != STATE_BOTH_SIGNED:
        return record
    if not signatures_satisfy(record["required_approvers"], record["signatures"]):
        return record
    before = {"state": record["state"], "quality_flag": record["quality_flag"]}
    append_audit(
        record,
        who="system",
        what=f"resolved {record['incident_id']} on option {record['option_id']}",
        why="both required signatures present; batch remains flagged for QA disposition",
        before=before,
        clock=clock,
    )
    record["state"] = STATE_RESOLVED
    return record


def is_resolved(record):
    return record["state"] == STATE_RESOLVED
