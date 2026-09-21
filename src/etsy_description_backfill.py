"""
Etsy Open API v3 description backfill for already-collected listings.


OUTPUT
------
Writes data/raw/descriptions.csv with columns: listing_id, description.
Kept separate from listings.csv on purpose, so this can't accidentally
clobber your existing collected data, join the two on listing_id in a
later step (e.g. features.py or a small merge script). Resumable: rerunning
skips listing_ids already in the output file, same pattern as
etsy_collector.py's resume support.

"""

import csv
import os
import sys
import time
from typing import Optional

import requests

API_BASE = "https://api.etsy.com/v3/application"
REQUEST_SLEEP_SECONDS = 0.4
MAX_RETRIES = 5
BATCH_SIZE = 100  # Etsy's documented max for listing_ids on the batch endpoint

LISTINGS_CSV = "data/raw/listings.csv"
OUTPUT_CSV = "data/raw/descriptions.csv"


class EtsyClient:
    def __init__(self, api_key: str, shared_secret: str):
        if not api_key or not shared_secret:
            raise ValueError(
                "Missing Etsy credentials. Set both the ETSY_API_KEY (keystring) "
                "and ETSY_SHARED_SECRET environment variables -- both are required "
                "to build the x-api-key header."
            )
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": f"{api_key}:{shared_secret}"})

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{API_BASE}{path}"
        for attempt in range(1, MAX_RETRIES + 1):
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                time.sleep(REQUEST_SLEEP_SECONDS)
                return resp.json()
            if resp.status_code in (429, 500, 502, 503):
                wait = min(2 ** attempt, 30)
                print(f"  [retry] {resp.status_code} on {path}, backing off {wait}s")
                time.sleep(wait)
                continue
            # Non-retryable error
            resp.raise_for_status()
        raise RuntimeError(f"Exceeded retries for {url}")

    def get_listings_by_ids(self, listing_ids: list) -> dict:
        params = {"listing_ids": ",".join(str(lid) for lid in listing_ids)}
        return self._get("/listings/batch", params=params)


def load_listing_ids(path: str) -> list:
    if not os.path.exists(path):
        print(f"Can't find {path} -- run etsy_collector.py first.")
        sys.exit(1)
    ids = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ids.append(row["listing_id"])
    return ids


def load_already_backfilled(path: str) -> set:
    if not os.path.exists(path):
        return set()
    seen = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seen.add(row["listing_id"])
    return seen


def backfill() -> None:
    api_key = os.environ.get("ETSY_API_KEY")
    shared_secret = os.environ.get("ETSY_SHARED_SECRET")
    client = EtsyClient(api_key, shared_secret)

    all_ids = load_listing_ids(LISTINGS_CSV)
    already_done = load_already_backfilled(OUTPUT_CSV)
    remaining = [lid for lid in all_ids if lid not in already_done]

    print(f"{len(all_ids)} listings total, {len(already_done)} already backfilled, "
          f"{len(remaining)} remaining.")
    if not remaining:
        print("Nothing to do.")
        return

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    write_header = not os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["listing_id", "description"])
        if write_header:
            writer.writeheader()

        for i in range(0, len(remaining), BATCH_SIZE):
            batch = remaining[i:i + BATCH_SIZE]
            try:
                data = client.get_listings_by_ids(batch)
            except requests.HTTPError as e:
                print(f"  HTTP error on batch starting at index {i}, skipping: {e}")
                continue

            results = data.get("results", [])
            found_ids = set()
            for listing in results:
                lid = str(listing.get("listing_id"))
                found_ids.add(lid)
                writer.writerow({
                    "listing_id": lid,
                    "description": listing.get("description") or "",
                })
            f.flush()

            missing = set(batch) - found_ids
            if missing:
                sample = list(missing)[:5]
                print(f"  [warn] {len(missing)} listing_ids in this batch returned "
                      f"nothing (likely sold out / removed since collection): "
                      f"{sample}{'...' if len(missing) > 5 else ''}")

            print(f"  ...{min(i + BATCH_SIZE, len(remaining))}/{len(remaining)} backfilled")

    print(f"Done. Wrote descriptions to {OUTPUT_CSV}")


if __name__ == "__main__":
    backfill()
