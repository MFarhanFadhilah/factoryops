import json
import sys
from pathlib import Path
import pytest

# Ensure tools directory is on sys.path
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from policy import evaluate_policy


# Load authoritative policy configuration from policy/action_policy.json
with open(REPO_ROOT / "policy" / "action_policy.json") as f:
    ACTION_POLICY = json.load(f)

ALWAYS_DENY_ACTIONS = ACTION_POLICY["always_deny"]
HUMAN_REQUIRED_ACTIONS = ACTION_POLICY["human_required"]
CONDITIONALLY_ALLOW_ACTIONS = ACTION_POLICY["conditionally_allow"]


# ---------------------------------------------------------------------------
# 1. DENY-always list: must return DENY regardless of any parameter combination
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("action", ALWAYS_DENY_ACTIONS)
@pytest.mark.parametrize("severity", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("evidence_complete", [True, False])
@pytest.mark.parametrize("user_role", [None, "operator", "admin", "qa_director"])
def test_always_deny_actions(action, severity, evidence_complete, user_role):
    res = evaluate_policy(
        proposed_action=action,
        severity=severity,
        evidence_complete=evidence_complete,
        user_role=user_role,
    )
    assert res["decision"] == "DENY"
    assert res["proposed_action"] == action
    assert "always_deny" in res["reason"]


# ---------------------------------------------------------------------------
# 2. CONTINUE_MONITORING: ALLOW when evidence_complete=True and low/medium severity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("severity", ["low", "medium"])
def test_continue_monitoring_allowed(severity):
    res = evaluate_policy(
        proposed_action="CONTINUE_MONITORING",
        severity=severity,
        evidence_complete=True,
    )
    assert res["decision"] == "ALLOW"
    assert res["proposed_action"] == "CONTINUE_MONITORING"
    assert "conditionally-allowed" in res["reason"]


# ---------------------------------------------------------------------------
# 3. CONTINUE_MONITORING: HUMAN_APPROVAL_REQUIRED when evidence_complete=False OR severity high/critical
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "severity,evidence_complete",
    [
        ("low", False),
        ("medium", False),
        ("high", True),
        ("critical", True),
        ("high", False),
        ("critical", False),
    ],
)
def test_continue_monitoring_escalated(severity, evidence_complete):
    res = evaluate_policy(
        proposed_action="CONTINUE_MONITORING",
        severity=severity,
        evidence_complete=evidence_complete,
    )
    assert res["decision"] == "HUMAN_APPROVAL_REQUIRED"
    assert res["proposed_action"] == "CONTINUE_MONITORING"


# ---------------------------------------------------------------------------
# 4. Human-required actions: must return HUMAN_APPROVAL_REQUIRED regardless of other inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("action", HUMAN_REQUIRED_ACTIONS)
@pytest.mark.parametrize("severity", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("evidence_complete", [True, False])
def test_human_required_actions(action, severity, evidence_complete):
    res = evaluate_policy(
        proposed_action=action,
        severity=severity,
        evidence_complete=evidence_complete,
    )
    assert res["decision"] == "HUMAN_APPROVAL_REQUIRED"
    assert res["proposed_action"] == action
    assert "human sign-off" in res["reason"]


# ---------------------------------------------------------------------------
# 5. Default-deny: unknown actions not in action_policy.json return DENY
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "unknown_action",
    [
        "UNKNOWN_ACTION",
        "REBOOT_PLC",
        "BYPASS_SAFETY_INTERLOCK",
        "SOME_RANDOM_STRING",
        "",
    ],
)
def test_unknown_action_default_deny(unknown_action):
    res = evaluate_policy(
        proposed_action=unknown_action,
        severity="low",
        evidence_complete=True,
    )
    assert res["decision"] == "DENY"
    assert "default-deny" in res["reason"]
