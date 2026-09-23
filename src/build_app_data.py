

import csv

LISTINGS_CSV = "data/processed/listings_with_descriptions.csv"
PROFILES_CSV = "data/processed/sustainability_profiles.csv"
OUTPUT_CSV = "data/processed/app_data.csv"

APP_FIELDNAMES = [
    "listing_id", "title", "price", "currency_code", "url", "image_url",
    "description", "materials", "certifications", "attributes",
    "is_vague_claim", "tier",
]


def load_profiles(path: str) -> dict:
    profiles = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            profiles[row["listing_id"]] = row
    return profiles


def build() -> None:
    profiles = load_profiles(PROFILES_CSV)

    with open(LISTINGS_CSV, newline="", encoding="utf-8") as f_in, \
         open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=APP_FIELDNAMES)
        writer.writeheader()

        written = 0
        for row in reader:
            profile = profiles.get(row["listing_id"])
            if not profile:
                continue
            writer.writerow({
                "listing_id": row["listing_id"],
                "title": row.get("title", ""),
                "price": row.get("price", ""),
                "currency_code": row.get("currency_code", ""),
                "url": row.get("url", ""),
                "image_url": row.get("image_url", ""),
                "description": row.get("description", ""),
                "materials": profile.get("materials", ""),
                "certifications": profile.get("certifications", ""),
                "attributes": profile.get("attributes", ""),
                "is_vague_claim": profile.get("is_vague_claim", ""),
                "tier": profile.get("tier", ""),
            })
            written += 1

    print(f"Wrote {written} listings to {OUTPUT_CSV}")


if __name__ == "__main__":
    build()
