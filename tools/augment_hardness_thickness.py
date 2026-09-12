"""One-off script to augment data/tablet_press_events.csv with hardness and thickness.

Derives:
- tablet_hardness_kp: baseline ~12.0 kp at 18.0 kN force, increasing roughly linearly
  with force (higher compression force = harder tablet), plus small gaussian noise (sigma ~0.3).
- tablet_thickness_mm: baseline ~4.50 mm at 18.0 kN force, decreasing roughly linearly
  with force (higher compression force = thinner tablet), plus small gaussian noise (sigma ~0.02).

Preserves all original columns and their original values and order, appending
tablet_hardness_kp and tablet_thickness_mm as the last two columns before
scenario_label and production_risk_score.
"""

import csv
from pathlib import Path
import random

# Fix random seed for reproducibility
random.seed(4242)

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "tablet_press_events.csv"


def augment_tablet_press_events(csv_path: Path = CSV_PATH):
    # 1. Read existing data
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        original_rows = list(reader)

    before_count = len(original_rows)

    # Validate existing header structure
    expected_tail = ["scenario_label", "production_risk_score"]
    if headers[-2:] != expected_tail:
        raise ValueError(f"Expected last two columns to be {expected_tail}, found: {headers[-2:]}")
    if "main_compression_force_kn" not in headers:
        raise ValueError("Missing 'main_compression_force_kn' column in CSV header.")

    force_idx = headers.index("main_compression_force_kn")

    # Construct new header: original columns except last 2, then new columns, then last 2
    new_headers = headers[:-2] + ["tablet_hardness_kp", "tablet_thickness_mm"] + headers[-2:]

    # 2. Derive new columns for each row
    augmented_rows = []
    for row in original_rows:
        force = float(row[force_idx])

        # tablet_hardness_kp: baseline ~12.0 kp at 18.0 kN force, slope ~0.7 kp/kN, sigma ~0.3
        hardness = 12.0 + 0.7 * (force - 18.0) + random.gauss(0.0, 0.3)

        # tablet_thickness_mm: baseline ~4.50 mm at 18.0 kN force, slope ~-0.04 mm/kN, sigma ~0.02
        thickness = 4.50 - 0.04 * (force - 18.0) + random.gauss(0.0, 0.02)

        new_row = row[:-2] + [round(hardness, 3), round(thickness, 3)] + row[-2:]
        augmented_rows.append(new_row)

    # 3. Overwrite file in place
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(new_headers)
        writer.writerows(augmented_rows)

    # 4. Read back and verify
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        written_headers = next(reader)
        written_rows = list(reader)

    after_count = len(written_rows)

    print(f"Before row count: {before_count}")
    print(f"After row count:  {after_count}")
    print(f"\nOriginal column count: {len(headers)}")
    print(f"New column count:      {len(written_headers)}")
    print("\nHeaders:")
    print("  " + ", ".join(written_headers))
    print("\nFirst 3 rows:")
    for i in range(min(3, after_count)):
        print(f"--- Row {i + 1} ---")
        for col_name, val in zip(written_headers, written_rows[i]):
            print(f"  {col_name}: {val}")


if __name__ == "__main__":
    augment_tablet_press_events()
