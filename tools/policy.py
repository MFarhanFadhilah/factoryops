import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import ACTION_POLICY_JSON


def _load_policy():
    with open(ACTION_POLICY_JSON) as f:
        return json.load(f)


def evaluate_policy(proposed_action, severity, evidence_complete, user_role=None):
    """Deterministic. Never model-decided: this is the enforcement gate, not the investigator."""
    policy = _load_policy()
    action = (proposed_action or "").upper()

    if action in policy["always_deny"]:
        return {
            "proposed_action": action,
            "decision": "DENY",
            "reason": "action is in the always_deny catalog and cannot be overridden",
        }

    if action in policy["human_required"]:
        return {
            "proposed_action": action,
            "decision": "HUMAN_APPROVAL_REQUIRED",
            "reason": "intervention requires human sign-off regardless of severity",
        }

    if action in policy["conditionally_allow"]:
        if not evidence_complete:
            return {
                "proposed_action": action,
                "decision": "HUMAN_APPROVAL_REQUIRED",
                "reason": "evidence incomplete; escalate to human approval rather than auto-allow",
            }
        if severity in ("high", "critical"):
            return {
                "proposed_action": action,
                "decision": "HUMAN_APPROVAL_REQUIRED",
                "reason": f"severity={severity} requires human approval even for conditionally-allowed actions",
            }
        return {
            "proposed_action": action,
            "decision": "ALLOW",
            "reason": "conditionally-allowed action with complete evidence and low/medium severity",
        }

    return {
        "proposed_action": action,
        "decision": policy["default"],
        "reason": "action not found in any catalog; default-deny",
    }


if __name__ == "__main__":
    for action in ("WRITE_PLC", "HOLD_AND_INSPECT", "CONTINUE_MONITORING", "RELEASE_BATCH"):
        print(action, "->", json.dumps(evaluate_policy(action, "medium", True)))
