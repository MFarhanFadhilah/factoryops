import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MAINTENANCE_CSV


def get_maintenance_history(machine_id, component=None):
    """Read-only. Returns work orders for a machine, optionally filtered by component substring."""
    records = []
    with open(MAINTENANCE_CSV, newline="") as f:
        for row in csv.DictReader(f):
            if row["machine_id"] != machine_id:
                continue
            if component and component.lower() not in row["component"].lower():
                continue
            records.append(dict(row))

    shutdown_hours = [
        float(r["hours_to_forced_shutdown"])
        for r in records
        if r.get("hours_to_forced_shutdown") and r["hours_to_forced_shutdown"].strip()
    ]
    mean_hours = (
        round(sum(shutdown_hours) / len(shutdown_hours), 2)
        if shutdown_hours
        else None
    )

    return {
        "machine_id": machine_id,
        "component_filter": component,
        "record_count": len(records),
        "mean_hours_to_forced_shutdown": mean_hours,
        "records": records,
    }


if __name__ == "__main__":
    print(json.dumps(get_maintenance_history("PRESS-RTP41-DEMO"), indent=2))
    print(json.dumps(get_maintenance_history("PRESS-RTP41-DEMO", component="feeder"), indent=2))
    print(json.dumps(get_maintenance_history("PRESS-RTP41-DEMO", component="bearing"), indent=2))
