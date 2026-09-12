import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import TELEMETRY_CSV, INCIDENTS_JSONL, BLIND_WINDOWS_JSON, DATA_DIR

# Columns coerced to float when present. Not every dataset has every column
# (the blind CSV has no scenario_label/production_risk_score) - only
# convert what's actually in the row, never assume a fixed schema.
_NUMERIC_FIELDS = (
    "main_compression_force_kn",
    "precompression_force_kn",
    "ejection_force_kn",
    "tablet_weight_mg",
    "turret_speed_rpm",
    "feeder_speed_rpm",
    "vibration_rms_mm_s",
    "bearing_temp_c",
    "tablet_hardness_kp",
    "tablet_thickness_mm",
    "production_risk_score",
)

# incidents.jsonl is the ONLY authoritative incident_id -> scenario mapping.
# It ships with the project data (Farhan's dataset), nothing invented here.
_NORMAL_BASELINE_ID = "INC-000"


def _parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_incidents_catalog():
    catalog = {}
    with open(INCIDENTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                entry = json.loads(line)
                catalog[entry["incident_id"]] = entry
    return catalog


def _scenario_for(incident_id):
    """Resolves incident_id -> (scenario_label, source_csv, machine_id).

    Two sources, both traceable:
    - INC-001..004 and INC-000 (normal baseline): scenario name comes from
      incidents.jsonl (or the "normal" convention for INC-000), looked up
      against the labeled tablet_press_events.csv.
    - INC-100+: the blind dataset has no scenario_label column by design,
      so its window boundaries are recorded in blind_dataset_windows.json,
      generated alongside the CSV itself (see that file's own comment).
    """
    if incident_id == _NORMAL_BASELINE_ID:
        return "normal", TELEMETRY_CSV, "PRESS-RTP41-DEMO"

    catalog = _load_incidents_catalog()
    if incident_id in catalog:
        return catalog[incident_id]["scenario"], TELEMETRY_CSV, "PRESS-RTP41-DEMO"

    if BLIND_WINDOWS_JSON.exists():
        with open(BLIND_WINDOWS_JSON) as f:
            blind = json.load(f)
        if incident_id in blind["incidents"]:
            entry = blind["incidents"][incident_id]
            return None, DATA_DIR / blind["source_csv"], entry["machine_id"], entry

    return None, None, None


def _load_label_series(csv_path, machine_id):
    series = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            if row["machine_id"] == machine_id:
                series.append((_parse_ts(row["timestamp"]), row.get("scenario_label")))
    return series


def _find_run_with_safe_padding(series, scenario_label, before_seconds, after_seconds):
    """Scans the CSV's own scenario_label column (in order) for the first
    contiguous run matching scenario_label - a real scan, not a lookup
    table. Then extends the window by up to before/after_seconds on each
    side, but NEVER past a row labeled as a *different* non-normal
    scenario: padding is meant to add a bit of surrounding context, not
    silently pull in a neighboring anomaly's data (e.g. the normal
    baseline sits directly before the first anomaly with no gap between
    them - padding after it must stop exactly at that boundary).
    """
    start_idx = end_idx = None
    for i, (_, label) in enumerate(series):
        if label == scenario_label:
            if start_idx is None:
                start_idx = i
            end_idx = i
        elif start_idx is not None:
            break

    if start_idx is None:
        return None, None

    def _safe(label):
        return label == scenario_label or label == "normal"

    left = start_idx
    while left > 0 and (start_idx - left) < before_seconds and _safe(series[left - 1][1]):
        left -= 1

    right = end_idx
    n = len(series)
    while right < n - 1 and (right - end_idx) < after_seconds and _safe(series[right + 1][1]):
        right += 1

    return series[left][0], series[right][0]


def _clamp_blind_padding(all_blind_incidents, target_id, before_seconds, after_seconds, data_bounds):
    """Same idea as _find_run_with_safe_padding, for the blind dataset:
    extend the declared window by up to before/after_seconds, but never
    past the boundary of another declared incident's window, and never
    past the actual first/last timestamp in the CSV.
    """
    target = all_blind_incidents[target_id]
    padded_start = _parse_ts(target["window_start"]) - timedelta(seconds=before_seconds)
    padded_end = _parse_ts(target["window_end"]) + timedelta(seconds=after_seconds)

    for other_id, other in all_blind_incidents.items():
        if other_id == target_id:
            continue
        other_start = _parse_ts(other["window_start"])
        other_end = _parse_ts(other["window_end"])
        if other_end < _parse_ts(target["window_start"]) and other_end + timedelta(seconds=1) > padded_start:
            padded_start = other_end + timedelta(seconds=1)
        if other_start > _parse_ts(target["window_end"]) and other_start - timedelta(seconds=1) < padded_end:
            padded_end = other_start - timedelta(seconds=1)

    data_start, data_end = data_bounds
    padded_start = max(padded_start, data_start)
    padded_end = min(padded_end, data_end)
    return padded_start, padded_end


def _series_bounds(csv_path, machine_id):
    series = _load_label_series(csv_path, machine_id)
    return series[0][0], series[-1][0]


def get_telemetry_window(incident_id, before_seconds=30, after_seconds=30):
    """Read-only. Returns raw telemetry rows covering an incident's actual
    event window, plus before_seconds/after_seconds of extra context on
    each side.

    For INC-000/INC-001..004: the window is the real contiguous block of
    matching scenario_label rows in tablet_press_events.csv, found by
    scanning the file - not a stored/guessed timestamp.
    For INC-100+ (blind dataset): boundaries come from
    blind_dataset_windows.json, since that CSV has no scenario_label to
    scan (that's the point of the blind test case).
    """
    resolved = _scenario_for(incident_id)
    if resolved[0] is None and resolved[1] is None:
        return {"incident_id": incident_id, "error": "unknown_incident_id", "rows": []}

    scenario_label, source_csv, machine_id, *rest = resolved

    if scenario_label is not None:
        series = _load_label_series(source_csv, machine_id)
        window_start, window_end = _find_run_with_safe_padding(
            series, scenario_label, before_seconds, after_seconds
        )
        if window_start is None:
            return {
                "incident_id": incident_id,
                "error": f"scenario_label '{scenario_label}' not found in {source_csv.name}",
                "rows": [],
            }
        provenance = f"scanned {source_csv.name} for scenario_label=='{scenario_label}', padding clamped to same/normal labels only"
    else:
        blind_entry = rest[0]
        with open(BLIND_WINDOWS_JSON) as f:
            all_blind = json.load(f)["incidents"]
        data_bounds = _series_bounds(source_csv, machine_id)
        window_start, window_end = _clamp_blind_padding(
            all_blind, incident_id, before_seconds, after_seconds, data_bounds
        )
        provenance = f"recorded in blind_dataset_windows.json ({blind_entry.get('note', '')}), padding clamped against neighboring declared windows"

    rows = []
    batch_id = None
    with open(source_csv, newline="") as f:
        for row in csv.DictReader(f):
            if row["machine_id"] != machine_id:
                continue
            ts = _parse_ts(row["timestamp"])
            if window_start <= ts <= window_end:
                batch_id = row["batch_id"]
                parsed = dict(row)
                for field in _NUMERIC_FIELDS:
                    if field in parsed:
                        parsed[field] = float(row[field])
                if "reject_flag" in parsed:
                    parsed["reject_flag"] = int(row["reject_flag"])
                rows.append(parsed)

    return {
        "incident_id": incident_id,
        "machine_id": machine_id,
        "batch_id": batch_id,
        "source_csv": Path(source_csv).name,
        "window_provenance": provenance,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "row_count": len(rows),
        "rows": rows,
    }


if __name__ == "__main__":
    for inc in ("INC-000", "INC-001", "INC-101"):
        result = get_telemetry_window(inc, before_seconds=5, after_seconds=5)
        print(inc, "->", result.get("window_provenance"), "| rows:", result.get("row_count"))
