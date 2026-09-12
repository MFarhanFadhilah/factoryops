import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import RULES_CONFIG_JSON
from anomaly_rules import evaluate_anomaly_rules


def _load_scoring():
    with open(RULES_CONFIG_JSON) as f:
        return json.load(f)["risk_scoring"]


def _severity_for(score, bands):
    for band in bands:
        if score >= band["floor"]:
            return band["label"]
    return "low"


def calculate_production_risk(incident_id):
    """Deterministic. Computes risk from triggered anomaly rules only —
    never reads a pre-labeled score column, so this works on any raw
    telemetry the rules can be evaluated against, labeled or not.
    """
    rules_result = evaluate_anomaly_rules(incident_id)
    if rules_result.get("error"):
        return {"incident_id": incident_id, "error": rules_result["error"]}

    scoring = _load_scoring()
    base_points = scoring["base_points"]
    max_bonus = scoring["max_overage_bonus"]
    cap_ratio = scoring["overage_cap_ratio"]

    contributions = []
    total = 0.0
    for rule in rules_result["triggered_rules"]:
        overage_ratio = min(max(rule.get("excess_ratio", 0.0), 0.0), cap_ratio)
        points = base_points[rule["severity"]] + overage_ratio * max_bonus
        contributions.append(
            {
                "rule_id": rule["rule_id"],
                "severity": rule["severity"],
                "excess_ratio": rule.get("excess_ratio", 0.0),
                "points": round(points, 2),
            }
        )
        total += points

    total = min(round(total, 2), 100.0)

    return {
        "incident_id": incident_id,
        "machine_id": rules_result["machine_id"],
        "batch_id": rules_result["batch_id"],
        "risk_score": total,
        "severity": _severity_for(total, scoring["severity_bands"]),
        "rule_contributions": contributions,
        "calculation_provenance": (
            "sum of base_points[severity] + overage bonus per triggered rule, "
            "from rules_config.json risk_scoring; computed from raw telemetry "
            "via evaluate_anomaly_rules, not read from any pre-labeled column"
        ),
    }


if __name__ == "__main__":
    for inc in ("INC-000", "INC-001", "INC-002", "INC-003", "INC-004"):
        r = calculate_production_risk(inc)
        print(inc, "->", r["risk_score"], r["severity"])
