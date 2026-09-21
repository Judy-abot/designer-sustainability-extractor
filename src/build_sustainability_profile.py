"""
Build one sustainability profile per listing: Certified / Specific claim /
Vague claim only / No signal, combining the rule-based dictionary
(material_extractor.py / run_extraction.py) with the zero-shot layer
(detect_vague_claims.py).

TIER LOGIC 
--------------------------------------
1. Certified             a named certification was found (GOTS, etc).
2. Specific claim        no certification, but a modifier-bearing material
                        (organic cotton, recycled polyester, deadstock
                        fabric, vegan leather, ...) or a meaningful
                        attribute (deadstock, upcycled, recycled, vegan)
                        was found. "Handmade" is deliberately excluded
                        here -- it's a craft-authenticity claim, not a
                        sustainability one, and including it would inflate
                        this tier with listings that aren't actually
                        making an environmental claim at all.
3. Vague claim only     no specific material/attribute/cert, but the
                        zero-shot layer flagged a general sustainability
                        claim (e.g. "kind to our environment"). This tier
                        IS the greenwashing flag from the original brief:
                        a real claim, with nothing specific behind it.
4. No signal            everything else: a bare material only (plain
                        "cotton", not a claim), or genuinely nothing
                        found by either layer. Swatch/sample listings
                        that were excluded from zero-shot classification
                        also land here by default, since they were never
                        actually asked the question.

A bare material (plain "cotton", "wool") on its own does NOT count as a
signal for tier 2, see material_extractor.py's own docstring: it's a
fabric name, not a claim.

Run from the project root:
    python3 src/build_sustainability_profile.py

Reads data/processed/extracted_signals.csv and
data/processed/vague_claim_signals.csv (the latter only covers listings
that had zero dictionary hits and weren't swatches -- missing from it is
expected and handled). Writes data/processed/sustainability_profiles.csv
and prints the tier distribution.
"""

import csv

from material_extractor import MATERIAL_PARENT

# Materials with an explicit sustainability-signaling qualifier attached
# (organic X, recycled X) plus deadstock fabric, which signals surplus-
# material reuse on its own with no generic "parent" to compare against.
# Deliberately excludes bare mentions of inherently-lower-impact fibers
# (hemp, bamboo, tencel, modal, linen) -- whether an unqualified mention
# of those counts as a "claim" is a genuinely debatable methodology call,
# and the conservative, defensible choice is not to count it without
# discussion, rather than quietly decide it either way.
SIGNAL_MATERIALS = set(MATERIAL_PARENT.keys()) | {"deadstock fabric"}

# Attributes that represent a real, specific sustainability-relevant
# claim. "Handmade" is excluded on purpose -- see module docstring.
MEANINGFUL_ATTRIBUTES = {"deadstock", "upcycled", "recycled", "vegan"}

SIGNALS_CSV = "data/processed/extracted_signals.csv"
VAGUE_CLAIMS_CSV = "data/processed/vague_claim_signals.csv"
OUTPUT_CSV = "data/processed/sustainability_profiles.csv"


def has_signal_material(materials_field: str) -> bool:
    materials = [m for m in materials_field.split("|") if m]
    return any(m in SIGNAL_MATERIALS for m in materials)


def has_meaningful_attribute(attributes_field: str) -> bool:
    attributes = [a for a in attributes_field.split("|") if a]
    return any(a in MEANINGFUL_ATTRIBUTES for a in attributes)


def load_vague_claims(path: str) -> dict:
    claims = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                claims[row["listing_id"]] = row["is_vague_claim"] == "True"
    except FileNotFoundError:
        print(f"[warn] {path} not found -- treating all as no vague-claim data")
    return claims


def build() -> None:
    vague_claims = load_vague_claims(VAGUE_CLAIMS_CSV)
    tier_counts = {"Certified": 0, "Specific claim": 0, "Vague claim only": 0, "No signal": 0}

    with open(SIGNALS_CSV, newline="", encoding="utf-8") as f_in, \
         open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["listing_id", "materials", "certifications", "attributes",
                      "is_vague_claim", "tier"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            is_vague = vague_claims.get(row["listing_id"])  # None if never classified

            if row["certifications"]:
                tier = "Certified"
            elif has_signal_material(row["materials"]) or has_meaningful_attribute(row["attributes"]):
                tier = "Specific claim"
            elif is_vague:
                tier = "Vague claim only"
            else:
                tier = "No signal"

            tier_counts[tier] += 1
            writer.writerow({
                "listing_id": row["listing_id"],
                "materials": row["materials"],
                "certifications": row["certifications"],
                "attributes": row["attributes"],
                "is_vague_claim": is_vague if is_vague is not None else "",
                "tier": tier,
            })

    total = sum(tier_counts.values())
    print("Sustainability profile tiers:")
    for tier in ["Certified", "Specific claim", "Vague claim only", "No signal"]:
        n = tier_counts[tier]
        print(f"  {tier}: {n}/{total} ({100 * n / total:.1f}%)")
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    build()
