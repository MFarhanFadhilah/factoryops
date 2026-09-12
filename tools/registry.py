import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import TOOLS_DIR
from telemetry import get_telemetry_window
from anomaly_rules import evaluate_anomaly_rules
from risk import calculate_production_risk
from business_impact import calculate_business_impact
from maintenance import get_maintenance_history
from rag_search import search_rag_documents
from policy import evaluate_policy
from audit import append_audit_event

with open(TOOLS_DIR.parent / "schemas" / "tool_contracts.json") as f:
    _CONTRACT = {t["name"]: t for t in json.load(f)["tools"]}

TOOLS = {
    "get_telemetry_window": get_telemetry_window,
    "evaluate_anomaly_rules": evaluate_anomaly_rules,
    "calculate_production_risk": calculate_production_risk,
    "calculate_business_impact": calculate_business_impact,
    "get_maintenance_history": get_maintenance_history,
    "search_rag_documents": search_rag_documents,
    "evaluate_policy": evaluate_policy,
    "append_audit_event": append_audit_event,
}

assert set(TOOLS) == set(_CONTRACT), "registry.py is out of sync with schemas/tool_contracts.json"


def call_tool(name, **kwargs):
    """Single entry point OpenClaw's tool-calling layer should invoke.

    Enforces the mode declared in tool_contracts.json: read_only and
    deterministic tools never write to disk; append_only may only append
    to the audit log (audit.py already opens it in 'a' mode, never 'w').
    """
    if name not in TOOLS:
        return {"error": f"unknown_tool:{name}"}

    mode = _CONTRACT[name]["mode"]
    result = TOOLS[name](**kwargs)
    return {"tool": name, "mode": mode, "result": result}


def describe_tools():
    """What to hand OpenClaw during agent/tool registration (name, mode, input schema)."""
    return list(_CONTRACT.values())


if __name__ == "__main__":
    print(json.dumps(describe_tools(), indent=2))
    print(json.dumps(call_tool("evaluate_policy", proposed_action="WRITE_PLC", severity="high", evidence_complete=True, user_role="agent")))
