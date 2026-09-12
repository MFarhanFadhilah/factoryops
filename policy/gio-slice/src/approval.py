from datetime import datetime, timezone

from policy_gate import ROLE_QA, ROLE_SUPERVISOR, signatures_satisfy

STATE_PRESENTED = "Presented"
STATE_SUPERVISOR_SIGNED = "SupervisorSigned"
STATE_BOTH_SIGNED = "BothSigned"
STATE_RESOLVED = "Resolved"
STATE_QA_HOLD = "QualityHold"

# A Deviation (continuing outside the approved limit) is not an intervention —
# nothing is being changed or repaired, so "approved" is the wrong word for
# what the Supervisor is signing. Distinct term, not a synonym: see
# AGENTS.md's rule against inventing new synonyms for things that already
# have a name. "Acknowledged" names a different act on purpose.
MEANING_SUPERVISOR = "intervention approved"
MEANING_SUPERVISOR_DEVIATION = "deviation acknowledged"
MEANING_QA = "batch disposition reviewed"
MEANING_QA_DENY = "batch disposition denied"

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


def supervisor_meaning(record):
    if record.get("change_type") == "Deviation":
        return MEANING_SUPERVISOR_DEVIATION
    return MEANING_SUPERVISOR


def sign_supervisor(record, name=SIGNER_SUPERVISOR_NAME, clock=None):
    if record["state"] != STATE_PRESENTED:
        return record
    if ROLE_SUPERVISOR not in record["required_approvers"]:
        return record
    if _has_role(record, ROLE_SUPERVISOR):
        return record
    before = {"state": record["state"], "signatures": [sig["role"] for sig in record["signatures"]]}
    timestamp = _iso(clock)
    meaning = supervisor_meaning(record)
    record["signatures"].append(
        {
            "role": ROLE_SUPERVISOR,
            "name": name,
            "meaning": meaning,
            "timestamp": timestamp,
        }
    )
    append_audit(
        record,
        who=name,
        what=f"signed option {record['option_id']} on {record['incident_id']}",
        why=f"{record['change_type']}: {meaning}",
        before=before,
        clock=clock,
    )
    _advance_if_complete(record)
    return record


def sign_qa(record, name=SIGNER_QA_NAME, decision="approve", reason=None, clock=None):
    """QA's judgment, not a rubber stamp: 21 CFR 211.22 gives the quality
    unit authority to approve OR reject. A denial requires a reason — see
    approval-forms-design's rule that rejections always carry a required
    comment and are never silently defaulted (unlike an approve, which
    doesn't need one to be a legitimate record).
    """
    if record["state"] != STATE_SUPERVISOR_SIGNED:
        return record
    if ROLE_QA not in record["required_approvers"]:
        return record
    if _has_role(record, ROLE_QA):
        return record
    if decision not in ("approve", "deny"):
        return record
    if decision == "deny" and not (reason and reason.strip()):
        return record
    before = {"state": record["state"], "signatures": [sig["role"] for sig in record["signatures"]]}
    timestamp = _iso(clock)
    meaning = MEANING_QA if decision == "approve" else MEANING_QA_DENY
    record["signatures"].append(
        {
            "role": ROLE_QA,
            "name": name,
            "meaning": meaning,
            "decision": decision,
            "reason": reason,
            "timestamp": timestamp,
        }
    )
    append_audit(
        record,
        who=name,
        what=(
            f"reviewed batch disposition for {record['incident_id']}"
            if decision == "approve"
            else f"denied batch disposition for {record['incident_id']}"
        ),
        why=reason if decision == "deny" else "21 CFR 211.22",
        before=before,
        clock=clock,
    )
    if decision == "deny":
        record["state"] = STATE_QA_HOLD
    else:
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


def can_sign(record, role):
    if role == ROLE_SUPERVISOR:
        return record["state"] == STATE_PRESENTED and not _has_role(record, ROLE_SUPERVISOR)
    if role == ROLE_QA:
        return record["state"] == STATE_SUPERVISOR_SIGNED and not _has_role(record, ROLE_QA)
    return False


def is_resolved(record):
    return record["state"] == STATE_RESOLVED


def is_on_hold(record):
    return record["state"] == STATE_QA_HOLD
