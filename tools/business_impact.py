import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import TOOLS_DIR

BUSINESS_CONFIG_JSON = TOOLS_DIR / "business_config.json"


def _load_config():
    with open(BUSINESS_CONFIG_JSON) as f:
        return json.load(f)


def calculate_business_impact(recommended_action):
    """Deterministic. tablets_at_risk = tablets_per_hour * downtime_hours;
    dollars_at_risk = tablets_at_risk / 1000 * contribution_margin - the
    exact formula from FactoryOps Requirements.pdf Step 6. Downtime hours
    per action are a synthetic estimate versioned in business_config.json,
    never invented per-call.
    """
    config = _load_config()
    action = (recommended_action or "").upper()
    downtime_hours = config["estimated_downtime_hours"].get(action)
    if downtime_hours is None:
        return {"error": f"unknown_action:{action}"}

    tablets_at_risk = config["tablets_per_hour"] * downtime_hours
    dollars_at_risk = round(
        tablets_at_risk / 1000 * config["contribution_margin_usd_per_1000_tablets"], 2
    )

    return {
        "recommended_action": action,
        "estimated_downtime_hours": downtime_hours,
        "tablets_at_risk": tablets_at_risk,
        "dollars_at_risk": dollars_at_risk,
        "calculation_provenance": (
            f"{config['tablets_per_hour']} tablets/hr x {downtime_hours}h downtime "
            f"x ${config['contribution_margin_usd_per_1000_tablets']}/1000 tablets "
            "(synthetic demo economics, see business_config.json)"
        ),
    }


if __name__ == "__main__":
    for action in (
        "CONTINUE_MONITORING", "HOLD_AND_SAMPLE", "HOLD_AND_INSPECT",
        "PAUSE_AND_INSPECT_TOOLING", "CONTROLLED_STOP_AND_MAINTENANCE_REVIEW",
    ):
        r = calculate_business_impact(action)
        print(action, "->", r["tablets_at_risk"], "tablets,", f"${r['dollars_at_risk']}")
