

import csv
import statistics
from collections import defaultdict

PROFILES_CSV = "data/processed/sustainability_profiles.csv"
LISTINGS_CSV = "data/processed/listings_with_descriptions.csv"

TIER_ORDER = ["Certified", "Specific claim", "Vague claim only", "No signal"]
SMALL_SAMPLE_THRESHOLD = 100


def load_tiers(path: str) -> dict:
    tiers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tiers[row["listing_id"]] = row["tier"]
    return tiers


def load_prices(path: str) -> list:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                price = float(row["price"])
            except (ValueError, KeyError):
                continue
            rows.append((row["listing_id"], price, row.get("currency_code", "")))
    return rows


def main() -> None:
    tiers = load_tiers(PROFILES_CSV)
    price_rows = load_prices(LISTINGS_CSV)

    currency_counts = defaultdict(int)
    for _, _, currency in price_rows:
        currency_counts[currency] += 1

    print("Currency distribution:")
    for currency, count in sorted(currency_counts.items(), key=lambda x: -x[1]):
        print(f"  {currency}: {count}")

    dominant_currency = max(currency_counts, key=currency_counts.get)
    excluded = sum(c for cur, c in currency_counts.items() if cur != dominant_currency)
    if excluded:
        print(f"\nRestricting comparison to {dominant_currency} only "
              f"({excluded} listings in other currencies excluded -- mixing "
              f"currencies in one average would be meaningless).\n")
    else:
        print(f"\nAll listings are in {dominant_currency}. No exclusions needed.\n")

    by_tier = defaultdict(list)
    for listing_id, price, currency in price_rows:
        if currency != dominant_currency:
            continue
        tier = tiers.get(listing_id)
        if tier:
            by_tier[tier].append(price)

    print(f"Median / mean price by tier ({dominant_currency}):")
    print(f"{'Tier':<20}{'n':>6}{'Median':>12}{'Mean':>12}")
    for tier in TIER_ORDER:
        prices = by_tier.get(tier, [])
        if not prices:
            continue
        median = statistics.median(prices)
        mean = statistics.mean(prices)
        print(f"{tier:<20}{len(prices):>6}{median:>12.2f}{mean:>12.2f}")

    n_certified = len(by_tier.get("Certified", []))
    if 0 < n_certified < SMALL_SAMPLE_THRESHOLD:
        print(f"\nCaveat: the Certified tier has only {n_certified} listings -- "
              f"treat any difference involving it as suggestive, not a firm "
              f"result. A couple of high- or low-priced outliers can swing "
              f"a median that size noticeably.")


if __name__ == "__main__":
    main()
