import json
import sys
from pathlib import Path
import pytest

# Ensure tools directory is on sys.path
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from _paths import AUDIT_LOG
from registry import describe_tools, call_tool, TOOLS


@pytest.fixture
def preserve_audit_log():
    """Ensure data/audit_log.jsonl state is preserved before and after tests."""
    existed = AUDIT_LOG.exists()
    content = AUDIT_LOG.read_bytes() if existed else None
    try:
        yield
    finally:
        if existed:
            AUDIT_LOG.write_bytes(content)
        elif AUDIT_LOG.exists():
            AUDIT_LOG.unlink()


# ---------------------------------------------------------------------------
# 1. describe_tools() matches schemas/tool_contracts.json
# ---------------------------------------------------------------------------

def test_describe_tools_matches_contract():
    contracts_file = REPO_ROOT / "schemas" / "tool_contracts.json"
    with open(contracts_file, "r", encoding="utf-8") as f:
        declared_tools = json.load(f)["tools"]

    described = describe_tools()

    assert len(described) == 8, f"Expected exactly 8 tools, got {len(described)}"
    assert len(declared_tools) == 8, f"Expected exactly 8 tools in contract, got {len(declared_tools)}"

    described_names = [t["name"] for t in described]
    declared_names = [t["name"] for t in declared_tools]
    assert described_names == declared_names, f"Tool names mismatch: {described_names} vs {declared_names}"

    # Verify each tool dictionary matches contract properties
    for desc, decl in zip(described, declared_tools):
        assert desc["name"] == decl["name"]
        assert desc["mode"] == decl["mode"]
        assert desc["input"] == decl["input"]


# ---------------------------------------------------------------------------
# 2. call_tool() with unknown tool returns error dict
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("unknown_name", ["unknown_tool_xyz", "non_existent_tool", "fake_tool", ""])
def test_call_tool_unknown_tool(unknown_name):
    res = call_tool(unknown_name)
    assert isinstance(res, dict)
    assert "error" in res
    assert res["error"] == f"unknown_tool:{unknown_name}"


# ---------------------------------------------------------------------------
# 3. call_tool() returns tool, mode, result for all 8 real tools
# ---------------------------------------------------------------------------

SAMPLE_TOOL_INPUTS = {
    "get_telemetry_window": {"incident_id": "INC-000", "before_seconds": 5, "after_seconds": 5},
    "evaluate_anomaly_rules": {"incident_id": "INC-000"},
    "calculate_production_risk": {"incident_id": "INC-000"},
    "calculate_business_impact": {"recommended_action": "CONTINUE_MONITORING"},
    "get_maintenance_history": {"machine_id": "PRESS-RTP41-DEMO"},
    "search_rag_documents": {"query": "tablet compression"},
    "evaluate_policy": {"proposed_action": "CONTINUE_MONITORING", "severity": "low", "evidence_complete": True},
    "append_audit_event": {
        "investigation": {"incident_id": "INC-000", "recommended_action": "CONTINUE_MONITORING"},
        "policy_decision": {"action": "CONTINUE_MONITORING", "decision": "ALLOW"},
        "human_decision": None,
    },
}


@pytest.mark.parametrize("tool_name", list(TOOLS.keys()))
def test_call_tool_real_tools(tool_name, preserve_audit_log):
    contracts_file = REPO_ROOT / "schemas" / "tool_contracts.json"
    with open(contracts_file, "r", encoding="utf-8") as f:
        contract_modes = {t["name"]: t["mode"] for t in json.load(f)["tools"]}

    expected_mode = contract_modes[tool_name]
    kwargs = SAMPLE_TOOL_INPUTS[tool_name]

    response = call_tool(tool_name, **kwargs)

    assert isinstance(response, dict), f"Expected dict response for {tool_name}, got {type(response)}"
    assert "tool" in response, f"Missing 'tool' key in response for {tool_name}"
    assert "mode" in response, f"Missing 'mode' key in response for {tool_name}"
    assert "result" in response, f"Missing 'result' key in response for {tool_name}"

    assert response["tool"] == tool_name
    assert response["mode"] == expected_mode
    assert isinstance(response["result"], dict)
    assert "error" not in response["result"], f"Unexpected error in result for {tool_name}: {response['result']}"
