import json
import sys
from pathlib import Path
import pytest

# Ensure tools directory is on sys.path
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from telemetry import get_telemetry_window
from anomaly_rules import evaluate_anomaly_rules
from risk import calculate_production_risk
from business_impact import calculate_business_impact
from maintenance import get_maintenance_history
from rag_search import search_rag_documents


# ---------------------------------------------------------------------------
# 1. get_telemetry_window
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("incident_id", ["INC-000", "INC-001", "INC-002", "INC-003", "INC-004"])
def test_get_telemetry_window_valid(incident_id):
    result = get_telemetry_window(incident_id, before_seconds=5, after_seconds=5)
    assert "error" not in result
    assert result["incident_id"] == incident_id
    assert result["row_count"] > 0
    assert len(result["rows"]) == result["row_count"]
    sample = result["rows"][0]
    assert isinstance(sample["main_compression_force_kn"], float)
    assert isinstance(sample["tablet_hardness_kp"], float)
    assert isinstance(sample["tablet_thickness_mm"], float)


def test_get_telemetry_window_invalid():
    result = get_telemetry_window("INC-999-DOES-NOT-EXIST")
    assert "error" in result
    assert result["incident_id"] == "INC-999-DOES-NOT-EXIST"
    assert result["rows"] == []


# ---------------------------------------------------------------------------
# 2. evaluate_anomaly_rules
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("incident_id", ["INC-000", "INC-001", "INC-002", "INC-003", "INC-004"])
def test_evaluate_anomaly_rules_valid(incident_id):
    result = evaluate_anomaly_rules(incident_id)
    assert "error" not in result
    assert result["incident_id"] == incident_id
    assert "triggered_rules" in result
    assert result["rows_evaluated"] > 0


def test_evaluate_anomaly_rules_invalid():
    result = evaluate_anomaly_rules("INC-999-DOES-NOT-EXIST")
    assert "error" in result
    assert result["incident_id"] == "INC-999-DOES-NOT-EXIST"
    assert result["triggered_rules"] == []


def test_evaluate_anomaly_rules_scenarios():
    # INC-000 (normal baseline) produces zero triggered rules
    res_normal = evaluate_anomaly_rules("INC-000")
    assert res_normal["triggered_rules"] == []

    # Map each incident to expected scenario and rules
    with open(REPO_ROOT / "data" / "incidents.jsonl") as f:
        incidents = {json.loads(line)["incident_id"]: json.loads(line)["scenario"] for line in f if line.strip()}

    with open(TOOLS_DIR / "rules_config.json") as f:
        rules_cfg = json.load(f)["rules"]

    scenario_to_rules = {}
    for r in rules_cfg:
        scenario_to_rules.setdefault(r["scenario"], []).append(r["rule_id"])

    # Confirm each of INC-001..INC-004 triggers at least the rule matching its own scenario
    for inc_id, scenario in incidents.items():
        res = evaluate_anomaly_rules(inc_id)
        triggered_ids = [r["rule_id"] for r in res["triggered_rules"]]
        expected_scenario_rules = scenario_to_rules[scenario]
        matching_triggered = [rid for rid in triggered_ids if rid in expected_scenario_rules]
        assert len(matching_triggered) > 0, (
            f"{inc_id} ({scenario}) expected to trigger rule(s) from {expected_scenario_rules}, got {triggered_ids}"
        )


# ---------------------------------------------------------------------------
# 3. calculate_production_risk
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("incident_id", ["INC-000", "INC-001", "INC-002", "INC-003", "INC-004"])
def test_calculate_production_risk_valid(incident_id):
    result = calculate_production_risk(incident_id)
    assert "error" not in result
    assert result["incident_id"] == incident_id
    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["severity"] in ("low", "medium", "high", "critical")
    assert "rule_contributions" in result


def test_calculate_production_risk_invalid():
    result = calculate_production_risk("INC-999-DOES-NOT-EXIST")
    assert "error" in result
    assert result["incident_id"] == "INC-999-DOES-NOT-EXIST"


# ---------------------------------------------------------------------------
# 4. calculate_business_impact
# ---------------------------------------------------------------------------

def test_calculate_business_impact_actions():
    # Load investigation.schema.json enum
    with open(REPO_ROOT / "schemas" / "investigation.schema.json") as f:
        schema = json.load(f)
    actions = schema["properties"]["recommended_action"]["enum"]

    # Load business_config.json
    with open(TOOLS_DIR / "business_config.json") as f:
        b_cfg = json.load(f)
    rate = b_cfg["tablets_per_hour"]
    margin = b_cfg["contribution_margin_usd_per_1000_tablets"]
    downtimes = b_cfg["estimated_downtime_hours"]

    for action in actions:
        res = calculate_business_impact(action)
        assert "error" not in res
        assert res["recommended_action"] == action
        expected_dt = downtimes[action]
        expected_tablets = rate * expected_dt
        expected_dollars = round(expected_tablets / 1000 * margin, 2)
        assert res["estimated_downtime_hours"] == expected_dt
        assert res["tablets_at_risk"] == expected_tablets
        assert res["dollars_at_risk"] == expected_dollars


def test_calculate_business_impact_invalid():
    res = calculate_business_impact("INVALID_ACTION_XYZ")
    assert "error" in res
    assert "unknown_action:INVALID_ACTION_XYZ" in res["error"]


# ---------------------------------------------------------------------------
# 5. get_maintenance_history
# ---------------------------------------------------------------------------

def test_get_maintenance_history_valid():
    res = get_maintenance_history("PRESS-RTP41-DEMO")
    assert "error" not in res
    assert res["machine_id"] == "PRESS-RTP41-DEMO"
    assert res["record_count"] > 0
    assert len(res["records"]) == res["record_count"]

    res_filtered = get_maintenance_history("PRESS-RTP41-DEMO", component="feeder")
    assert "error" not in res_filtered
    assert all("feeder" in r["component"].lower() for r in res_filtered["records"])


def test_get_maintenance_history_unknown():
    res = get_maintenance_history("MACHINE-DOES-NOT-EXIST")
    assert "error" not in res
    assert res["record_count"] == 0
    assert res["records"] == []


# ---------------------------------------------------------------------------
# 6. search_rag_documents
# ---------------------------------------------------------------------------

def test_search_rag_documents_valid():
    res = search_rag_documents("compression force hardness thickness")
    assert "error" not in res
    assert res["integrity_issues"] == []
    assert res["result_count"] > 0
    assert len(res["results"]) == res["result_count"]
    first = res["results"][0]
    assert "document" in first
    assert "chunk" in first
    assert "score" in first
    assert "excerpt" in first


def test_search_rag_documents_empty_filter():
    res = search_rag_documents("tablet", document_types=["non_existent_type"])
    assert res["results"] == []
    assert "note" in res
