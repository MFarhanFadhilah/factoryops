"""Generates tablet_press_events_blind.csv - a synthetic telemetry stream
with NO scenario_label or production_risk_score columns, unlike the main
tablet_press_events.csv. Its purpose is to prove the FactoryOps
tools detect and score anomalies from raw sensor thresholds alone, never
by reading a pre-labeled answer-key column.

The SEGMENTS list below is the single source of truth for where each
anomaly was injected. blind_dataset_windows.json's window_start/window_end
values are copied directly from this list - re-run this script and update
that file together if you ever change the segments.
"""

import csv
import random
from datetime import datetime, timedelta, timezone

random.seed(4242)

MACHINE = "PRESS-RTP41-DEMO"
BATCH = "BATCH-DEMO-002"
START = datetime(2026, 9, 13, 9, 0, 0, tzinfo=timezone.utc)
TOTAL_SECONDS = 45 * 60

# (start_offset_seconds, end_offset_seconds, kind) - end is exclusive.
# Gaps between segments (and before the first / after the last) are normal.
SEGMENTS = [
    (300, 600, "force"),        # 09:05:00-09:09:59
    (900, 1200, "weight"),      # 09:15:00-09:19:59
    (1500, 1800, "eject"),      # 09:25:00-09:29:59
    (2100, 2400, "vibration"),  # 09:35:00-09:39:59
]

FIELDS = [
    "timestamp", "machine_id", "batch_id",
    "main_compression_force_kn", "precompression_force_kn", "ejection_force_kn",
    "tablet_weight_mg", "turret_speed_rpm", "feeder_speed_rpm",
    "vibration_rms_mm_s", "bearing_temp_c",
    "tablet_hardness_kp", "tablet_thickness_mm", "reject_flag",
]


def _segment_kind(offset_seconds):
    for start, end, kind in SEGMENTS:
        if start <= offset_seconds < end:
            return kind
    return "normal"


def generate(out_path):
    rows = []
    for offset in range(TOTAL_SECONDS):
        kind = _segment_kind(offset)
        ts = START + timedelta(seconds=offset)

        force = random.gauss(18.0, 0.4)
        precompression = random.gauss(3.5, 0.1)
        eject = random.gauss(0.65, 0.05)
        weight = random.gauss(500.0, 2.5)
        turret = random.gauss(45.0, 0.3)
        feeder = random.gauss(32.0, 0.3)
        vibration = random.gauss(1.2, 0.1)
        bearing = random.gauss(31.0, 0.2)
        reject = 0

        if kind == "force":
            force = random.gauss(23.0, 1.2)
            reject = 1
        elif kind == "weight":
            weight = random.gauss(500.0, 9.0)
            reject = 1 if abs(weight - 500.0) > 10 else 0
        elif kind == "eject":
            eject = random.gauss(1.4, 0.25)
            reject = 1
        elif kind == "vibration":
            vibration = random.gauss(2.6, 0.4)
            bearing = random.gauss(33.0, 0.7)
            reject = 1

        # tablet_hardness_kp: baseline ~12.0 kp at 18.0 kN force, slope ~0.7 kp/kN, sigma ~0.3
        hardness = 12.0 + 0.7 * (force - 18.0) + random.gauss(0.0, 0.3)

        # tablet_thickness_mm: baseline ~4.50 mm at 18.0 kN force, slope ~-0.04 mm/kN, sigma ~0.02
        thickness = 4.50 - 0.04 * (force - 18.0) + random.gauss(0.0, 0.02)

        rows.append([
            ts.isoformat(), MACHINE, BATCH,
            round(force, 3), round(precompression, 3), round(eject, 3),
            round(weight, 3), round(turret, 3), round(feeder, 3),
            round(vibration, 3), round(bearing, 3),
            round(hardness, 3), round(thickness, 3), reject,
        ])

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    from _paths import BLIND_TELEMETRY_CSV

    count = generate(BLIND_TELEMETRY_CSV)
    print(f"wrote {count} rows to {BLIND_TELEMETRY_CSV}")
