
import csv
import os

LISTINGS_CSV = "data/raw/listings.csv"
DESCRIPTIONS_CSV = "data/raw/descriptions.csv"
OUTPUT_CSV = "data/processed/listings_with_descriptions.csv"


def load_descriptions(path: str) -> dict:
    descriptions = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            descriptions[row["listing_id"]] = row["description"]
    return descriptions


def join() -> None:
    descriptions = load_descriptions(DESCRIPTIONS_CSV)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(LISTINGS_CSV, newline="", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames + ["description"]

        matched = 0
        total = 0
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                total += 1
                desc = descriptions.get(row["listing_id"], "")
                if desc:
                    matched += 1
                row["description"] = desc
                writer.writerow(row)

    print(f"Joined {matched}/{total} listings with a description.")
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    join()
