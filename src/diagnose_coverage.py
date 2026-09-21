"""
Diagnostic on run_extraction.py's output.

Run from the project root:
    python3 src/diagnose_coverage.py
"""

import csv
import random

from material_extractor import MATERIAL_PARENT

# Every material that requires an explicit modifier word to match at all
# (see MATERIAL_PARENT in material_extractor.py) -- these are the ones
# that represent a real, specific sustainability signal.
MODIFIER_MATERIALS = set(MATERIAL_PARENT.keys())

SIGNALS_CSV = "data/processed/extracted_signals.csv"
JOINED_CSV = "data/processed/listings_with_descriptions.csv"
SAMPLE_SIZE = 8


def main() -> None:
    with_modifier = 0
    bare_only = 0
    no_material = 0
    no_match_ids = []

    with open(SIGNALS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            materials = [m for m in row["materials"].split("|") if m]
            if any(m in MODIFIER_MATERIALS for m in materials):
                with_modifier += 1
            elif materials:
                bare_only += 1
            else:
                no_material += 1
            if not materials and not row["certifications"] and not row["attributes"]:
                no_match_ids.append(row["listing_id"])

    total = with_modifier + bare_only + no_material

    def pct(n):
        return f"{n}/{total} ({100 * n / total:.1f}%)"

    print("Material match, broken down:")
    print(f"  Modifier-bearing (a real signal): {pct(with_modifier)}")
    print(f"  Bare material only (not a claim):  {pct(bare_only)}")
    print(f"  No material match:                 {pct(no_material)}")
    print()

    print(f"No-match listings: {len(no_match_ids)}. "
          f"Sampling up to {SAMPLE_SIZE} for a look at their text:\n")

    sample_ids = set(random.sample(no_match_ids, min(SAMPLE_SIZE, len(no_match_ids))))
    shown = 0
    with open(JOINED_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["listing_id"] in sample_ids:
                shown += 1
                print(f"[{row['listing_id']}] {row.get('title', '')}")
                print(f"  materials field: {row.get('materials', '')!r}")
                desc = (row.get("description", "") or "").strip().replace("\n", " ")
                print(f"  description: {desc[:200]}{'...' if len(desc) > 200 else ''}")
                print()
                if shown >= SAMPLE_SIZE:
                    break


if __name__ == "__main__":
    main()
