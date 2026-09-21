"""
Sustainability Intelligence -- Streamlit app.

Filters and displays the 4,500 listings by sustainability tier
(Certified / Specific claim / Vague claim only / No signal), showing the
extracted materials/certifications/attributes next to the original
listing text so the extraction can be checked against the source rather
than trusted blindly.

Run from the project root:
    streamlit run app.py

Expects:
    data/processed/listings_with_descriptions.csv
    data/processed/sustainability_profiles.csv

NOTE ON TESTING
----------------
This environment can't run a Streamlit server, so the UI itself (layout,
widgets) hasn't been visually verified -- it follows the same st.* patterns
your Projects 1 and 2 apps already use successfully. What WAS tested here:
the data loading and merge logic. Two real bugs were caught and fixed
before this ever touched the UI code:
  1. Both source files have a `materials` column with different meaning
     (raw Etsy field vs. extracted canonical list) -- a naive merge would
     have silently renamed them to materials_x/materials_y and broken
     every reference to `materials` in the display code.
  2. An empty materials/certifications/attributes cell comes back from
     pandas as NaN, not an empty string -- splitting that naively would
     have displayed the literal text "nan" as a fake material.
Both are handled below (see load_data()). Run it and tell me what breaks,
if anything, in the parts I couldn't test myself.
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sustainability Intelligence", layout="wide")

LISTINGS_PATH = "data/processed/listings_with_descriptions.csv"
PROFILES_PATH = "data/processed/sustainability_profiles.csv"

TIER_ORDER = ["Certified", "Specific claim", "Vague claim only", "No signal"]
TIER_ICONS = {
    "Certified": "\U0001F7E2",
    "Specific claim": "\U0001F7E1",
    "Vague claim only": "\U0001F7E0",
    "No signal": "\u26AA",
}


@st.cache_data
def load_data() -> pd.DataFrame:
    listings = pd.read_csv(LISTINGS_PATH, dtype={"listing_id": str})
    profiles = pd.read_csv(PROFILES_PATH, dtype={"listing_id": str})

    # Both files have a `materials` column with different meanings (raw
    # Etsy field vs. extracted canonical list) -- rename before merging so
    # pandas doesn't silently turn both into materials_x/materials_y.
    listings = listings.rename(columns={"materials": "raw_materials"})
    merged = listings.merge(profiles, on="listing_id", how="inner")

    # Empty cells come back as NaN, not "" -- fill these before any
    # string splitting downstream, or NaN prints as the literal text "nan".
    for col in ["materials", "certifications", "attributes"]:
        merged[col] = merged[col].fillna("")

    return merged


def split_field(value: str) -> list:
    return [v for v in str(value).split("|") if v]


def main() -> None:
    st.title("Sustainability Intelligence")
    st.caption(
        "Structured material and certification signals extracted from Etsy "
        "handmade-clothing listings. Every extraction is shown next to the "
        "original listing text -- verify it, don't just trust it."
    )

    df = load_data()

    with st.sidebar:
        st.header("Filters")
        selected_tiers = st.multiselect("Sustainability tier", options=TIER_ORDER, default=TIER_ORDER)
        search = st.text_input("Search title", "")

        all_materials = sorted({m for materials in df["materials"] for m in split_field(materials)})
        selected_materials = st.multiselect("Material contains", options=all_materials)

    filtered = df[df["tier"].isin(selected_tiers)]
    if search:
        filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]
    if selected_materials:
        filtered = filtered[filtered["materials"].apply(
            lambda m: any(sel in split_field(m) for sel in selected_materials)
        )]

    st.write(f"**{len(filtered)}** of {len(df)} listings match your filters.")

    tier_counts = df["tier"].value_counts().reindex(TIER_ORDER, fill_value=0)
    st.bar_chart(tier_counts)

    st.divider()

    for _, row in filtered.head(50).iterrows():
        with st.container(border=True):
            cols = st.columns([1, 3])
            with cols[0]:
                image_url = row.get("image_url", "")
                if isinstance(image_url, str) and image_url:
                    st.image(image_url, use_container_width=True)
            with cols[1]:
                tier = row["tier"]
                st.markdown(f"### {TIER_ICONS.get(tier, '')} {row['title']}")
                st.markdown(f"**Tier:** {tier}  |  **Price:** {row.get('price', '?')} {row.get('currency_code', '')}")

                materials = split_field(row["materials"])
                certs = split_field(row["certifications"])
                attrs = split_field(row["attributes"])

                if materials:
                    st.markdown(f"**Materials found:** {', '.join(materials)}")
                if certs:
                    st.markdown(f"**Certifications found:** {', '.join(certs)}")
                if attrs:
                    st.markdown(f"**Attributes found:** {', '.join(attrs)}")
                if str(row.get("is_vague_claim", "")) == "True":
                    st.markdown("**Zero-shot flag:** general sustainability language detected, no specifics named")

                with st.expander("Original listing text"):
                    st.write(row.get("description", ""))

                url = row.get("url", "")
                if isinstance(url, str) and url:
                    st.markdown(f"[View on Etsy]({url})")

    if len(filtered) > 50:
        st.caption(f"Showing the first 50 of {len(filtered)} matches.")


if __name__ == "__main__":
    main()
