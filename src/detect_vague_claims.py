"""
Zero-shot detection of vague/general sustainability claims, run ONLY on
the listings material_extractor.py found nothing specific in.

Why only the no-match subset, not all 4,500: the diagnostic
(diagnose_coverage.py) showed the rule-based dictionary already catches
the actual, specific claims (organic cotton, GOTS, deadstock, etc) at
204/4500, and an 8-listing sample of the no-match group showed most of it
is genuinely unrelated content (style, fit, occasion), not vague
sustainability language slipping past the keywords. Running an expensive
model over every listing to re-confirm what a keyword search already
settled -- or to find nothing on listings that have nothing to find --
wastes time for no benefit. This model earns its keep specifically on the
no-match subset, to tell apart two different things within it:
  - genuinely unrelated content (most of the sample looked like this)
  - a real but vague sustainability claim with no specific material/cert
    named ("kind to our environment", "sustainable fashion")

NOTE ON TESTING
---------------
This uses the `transformers` zero-shot-classification pipeline
(facebook/bart-large-mnli), which downloads the model from Hugging Face on
first run -- not reachable from this sandboxed environment, so I couldn't
run this one end-to-end myself the way I did the earlier scripts. The
surrounding CSV read/filter logic is the same pattern already verified in
run_extraction.py and was tested separately; the model call itself follows
the standard, documented transformers pipeline usage. Run the --limit
version first to confirm it works before committing to the full run.

SETUP
-----
Already installed and confirmed working (transformers 4.57.6, torch 2.2.2).
First run downloads the model, ~1.6GB -- only happens once, then it's
cached locally.

Run from the project root:
    python3 src/detect_vague_claims.py --limit 20   # quick smoke test first
    python3 src/detect_vague_claims.py               # full run

Reads data/processed/listings_with_descriptions.csv and
data/processed/extracted_signals.csv. Writes
data/processed/vague_claim_signals.csv (listing_id, is_vague_claim,
confidence) for the no-match subset only.
"""

import argparse
import csv
import re

URL_PATTERN = re.compile(r"https?://\S+")
# Fabric swatch/color-sample listings ("Sample", "swatch", "color card")
# aren't finished garments -- a "which color do you want" listing doesn't
# meaningfully make or fail to make a sustainability claim the way a real
# garment listing does. Confirmed on a real false positive: a tulle color
# swatch scored 0.918 as a sustainability claim even after URL cleanup,
# with essentially no relevant content in the text at all. Project 1's
# collector already tries to exclude supply/component listings via Etsy's
# is_supply flag, but this one slipped through -- Etsy's own flag isn't
# fully reliable, so this is a second, text-based pass at the same intent.
SWATCH_SAMPLE_PATTERN = re.compile(
    r"\bswatch\b|\bcolor\s*sample\b|\bcolour\s*sample\b|\bcolor\s*card\b|\bcolour\s*card\b",
    re.IGNORECASE,
)

CANDIDATE_LABEL = "a sustainability or eco-friendly claim"
CLAIM_THRESHOLD = 0.5
# multi_label=True scores this one label independently, as its own yes/no
# question, instead of forcing it to compete against a second label. An
# earlier version used two competing labels ("a sustainability claim" vs
# "no sustainability claim") -- but the second one reads as an awkward,
# incomplete sentence once the model's default template wraps it ("This
# example is no sustainability claim."), which biased results toward the
# better-formed first label regardless of the actual text. Confirmed on a
# 20-listing smoke test: a listing whose entire description was "Additional
# items" scored 0.868 on the two-label version -- a near-empty string
# should never score that confidently as a claim, so the label-competition
# framing, not the model, was producing the skew.

SIGNALS_CSV = "data/processed/extracted_signals.csv"
JOINED_CSV = "data/processed/listings_with_descriptions.csv"
OUTPUT_CSV = "data/processed/vague_claim_signals.csv"


def load_no_match_ids(path: str) -> set:
    ids = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["materials"] and not row["certifications"] and not row["attributes"]:
                ids.add(row["listing_id"])
    return ids


def load_texts(path: str, wanted_ids: set) -> tuple:
    rows = []
    skipped_swatches = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["listing_id"] not in wanted_ids:
                continue
            title = row.get("title", "") or ""
            tags = row.get("tags", "") or ""
            if SWATCH_SAMPLE_PATTERN.search(title) or SWATCH_SAMPLE_PATTERN.search(tags):
                skipped_swatches += 1
                continue
            text = " ".join([title, row.get("description", "") or ""])
            # Strip raw URLs before classification -- confirmed on a real
            # false positive that leaving them in can produce a
            # confidently wrong score; URLs carry no sustainability-
            # relevant meaning.
            text = URL_PATTERN.sub("", text)
            text = re.sub(r"\s+", " ", text).strip()
            rows.append((row["listing_id"], text))
    return rows, skipped_swatches


def main(limit=None) -> None:
    from transformers import pipeline

    no_match_ids = load_no_match_ids(SIGNALS_CSV)
    texts, skipped_swatches = load_texts(JOINED_CSV, no_match_ids)
    if limit:
        texts = texts[:limit]

    print(f"Classifying {len(texts)} listings with no dictionary match "
          f"({skipped_swatches} swatch/sample listings excluded)...")
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["listing_id", "is_vague_claim", "confidence"])
        writer.writeheader()
        for i, (listing_id, text) in enumerate(texts):
            if not text:
                writer.writerow({"listing_id": listing_id, "is_vague_claim": False, "confidence": 0.0})
                continue
            result = classifier(text[:1000], [CANDIDATE_LABEL], multi_label=True)
            score = result["scores"][0]
            is_claim = score > CLAIM_THRESHOLD
            writer.writerow({
                "listing_id": listing_id,
                "is_vague_claim": is_claim,
                "confidence": round(score, 3),
            })
            if (i + 1) % 50 == 0:
                print(f"  ...{i + 1}/{len(texts)}")

    print(f"Done. Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only classify the first N no-match listings (for a quick test run)",
    )
    args = parser.parse_args()
    main(limit=args.limit)
