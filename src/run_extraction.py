"""
Apply material_extractor.extract_signals() across the full joined dataset
and report coverage stats -- how many listings got a specific material,
a certification, or a specific attribute hit, versus none at all.

This is the empirical check for Open Question #2: whether the rule-based
dictionary alone gets meaningful coverage on listing text, or whether a
large share of "no signal" listings are actually the vague-claim gap the
zero-shot layer is meant to close, rather than genuinely having nothing
sustainability-related to say.

Run from the project root:
    python3 src/run_extraction.py

Writes data/processed/extracted_signals.csv (one row per listing, with
materials/certifications/attributes as pipe-joined strings) and prints
summary coverage stats to the terminal.
"""

import csv
import os

from material_extractor import extract_signals

INPUT_CSV = "data/processed/listings_with_descriptions.csv"
OUTPUT_CSV = "data/processed/extracted_signals.csv"


def run() -> None:
    with open(INPUT_CSV, newline="", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    fieldnames = ["listing_id", "materials", "certifications", "attributes"]

    total = len(rows)
    with_material = 0
    with_cert = 0
    with_attribute = 0
    with_any = 0

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            signals = extract_signals(
                title=row.get("title", ""),
                materials=row.get("materials", ""),
                tags=row.get("tags", ""),
                description=row.get("description", ""),
            )
            if signals["materials"]:
                with_material += 1
            if signals["certifications"]:
                with_cert += 1
            if signals["attributes"]:
                with_attribute += 1
            if signals["materials"] or signals["certifications"] or signals["attributes"]:
                with_any += 1

            writer.writerow({
                "listing_id": row["listing_id"],
                "materials": "|".join(signals["materials"]),
                "certifications": "|".join(signals["certifications"]),
                "attributes": "|".join(signals["attributes"]),
            })

    def pct(n):
        return f"{n}/{total} ({100 * n / total:.1f}%)"

    print(f"Total listings: {total}")
    print(f"  With a material match:      {pct(with_material)}")
    print(f"  With a certification match: {pct(with_cert)}")
    print(f"  With an attribute match:    {pct(with_attribute)}")
    print(f"  With any match at all:      {pct(with_any)}")
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    run()
