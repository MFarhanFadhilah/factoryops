import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import RULES_CONFIG_JSON
from telemetry import get_telemetry_window


def _load_rules():
    with open(RULES_CONFIG_JSON) as f:
        config = json.load(f)
    return config["rules"], config.get("min_sustained_seconds", 3)


def _max_consecutive_run(flags):
    best = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        best = max(best, current)
    return best


def _check_rule(rule, rows, min_sustained_seconds):
    metric = rule["metric"]
    values = [row[metric] for row in rows if metric in row]
    if not values:
        return None

    if rule["comparator"] == "gt":
        breach_flags = [v > rule["threshold"] for v in values]
        observed = max(values)
    elif rule["comparator"] == "abs_deviation_gt":
        deviations = [abs(v - rule["target"]) for v in values]
        breach_flags = [d > rule["threshold"] for d in deviations]
        observed = max(deviations)
    else:
        return None

    sustained_seconds = _max_consecutive_run(breach_flags)
    # A single noisy sample must not fire a rule - require a sustained run,
    # not just any value crossing the line (rows are one-second cadence).
    triggered = sustained_seconds >= min_sustained_seconds

    if not triggered:
        return {
            "rule_id": rule["rule_id"],
            "triggered": False,
            "observed_value": round(observed, 3),
            "threshold": rule["threshold"],
            "sustained_seconds": sustained_seconds,
        }

    excess_ratio = (observed - rule["threshold"]) / rule["threshold"] if rule["threshold"] else 0.0

    return {
        "rule_id": rule["rule_id"],
        "triggered": True,
        "observed_value": round(observed, 3),
        "configured_threshold": rule["threshold"],
        "excess_ratio": round(excess_ratio, 4),
        "unit": rule["unit"],
        "duration_seconds": sustained_seconds,
        "severity": rule["severity"],
        "description": rule["description"],
        "calculation_provenance": {
            "metric": metric,
            "comparator": rule["comparator"],
            "sample_size": len(values),
            "mean_observed": round(statistics.mean(values), 3),
            "min_sustained_seconds_required": min_sustained_seconds,
        },
    }


def evaluate_anomaly_rules(incident_id):
    """Read-only. Deterministic rule evaluation; thresholds live in rules_config.json, not in prompts."""
    # 30s of context on each side of the real event block that
    # get_telemetry_window finds by scanning scenario_label - the anomaly
    # itself is already fully captured, this just adds transition context.
    telemetry = get_telemetry_window(incident_id, before_seconds=30, after_seconds=30)
    if telemetry.get("error"):
        return {"incident_id": incident_id, "error": telemetry["error"], "triggered_rules": []}

    rules, min_sustained_seconds = _load_rules()
    triggered = []
    for rule in rules:
        result = _check_rule(rule, telemetry["rows"], min_sustained_seconds)
        if result and result["triggered"]:
            triggered.append(result)

    return {
        "incident_id": incident_id,
        "machine_id": telemetry["machine_id"],
        "batch_id": telemetry["batch_id"],
        "rows_evaluated": telemetry["row_count"],
        "triggered_rules": triggered,
    }


if __name__ == "__main__":
    for inc in ("INC-001", "INC-002", "INC-003", "INC-004"):
        print(inc, "->", json.dumps(evaluate_anomaly_rules(inc)["triggered_rules"]))
