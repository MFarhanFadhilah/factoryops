import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import AUDIT_LOG


def append_audit_event(investigation, policy_decision, human_decision=None):
    """Append-only. Never rewrites or deletes prior entries; only opens the log in append mode."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "incident_id": investigation.get("incident_id"),
        "machine_id": investigation.get("machine_id"),
        "batch_id": investigation.get("batch_id"),
        "recommended_action": investigation.get("recommended_action"),
        "citations": investigation.get("citations", []),
        "policy_decision": policy_decision,
        "human_decision": human_decision,
    }

    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")

    return {"appended": True, "event": event}


def read_audit_log():
    """Convenience for the UI/audit panel; not part of the agent's typed tool contract."""
    if not AUDIT_LOG.exists():
        return []
    with open(AUDIT_LOG) as f:
        return [json.loads(line) for line in f if line.strip()]


if __name__ == "__main__":
    sample_investigation = {
        "incident_id": "INC-001",
        "machine_id": "PRESS-RTP41-DEMO",
        "batch_id": "BATCH-DEMO-001",
        "recommended_action": "HOLD_AND_INSPECT",
        "citations": [{"document": "SOP-DEMO-001_Anomaly_Triage.md", "page": None, "chunk": "c0"}],
    }
    print(json.dumps(append_audit_event(sample_investigation, "HUMAN_APPROVAL_REQUIRED", {"approved": True})))
    print("log now has", len(read_audit_log()), "entries")
