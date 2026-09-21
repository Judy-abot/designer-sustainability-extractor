"""
Rule-based extraction of material composition and sustainability
certifications from Etsy listing text (title + tags + materials +
description).
USAGE
-----
from material_extractor import extract_signals

signals = extract_signals(
    title="Deadstock Organic Cotton Jersey Dress",
    materials="organic cotton",
    tags="handmade|sustainable|deadstock",
    description="Content: 100% Organic Cotton. GOTS certified.",
)
# signals == {
#     "materials": ["organic cotton"],
#     "certifications": ["GOTS"],
#     "attributes": ["deadstock"],
# }
"""

import re

# --- Materials ---------------------------------------------------------
# Canonical material -> regex patterns that should match it. Dict order
# matters here: more specific entries (e.g. "organic cotton") are checked
# before their generic parent ("cotton"), and MATERIAL_PARENT below makes
# sure a specific hit suppresses its generic parent from also firing on
# the same text (so "organic cotton" text doesn't also list plain "cotton").
MATERIAL_PATTERNS = {
    "organic cotton": [r"organic\s+cotton"],
    "recycled polyester": [r"recycled\s+poly(?:ester)?", r"\brpet\b"],
    "recycled nylon": [r"recycled\s+nylon"],
    "recycled wool": [r"recycled\s+wool"],
    "deadstock fabric": [r"dead\s?stock"],
    "tencel / lyocell": [r"\btencel\b", r"\blyocell\b"],
    "modal": [r"\bmodal\b"],
    "hemp": [r"\bhemp\b"],
    "bamboo": [r"\bbamboo\b"],
    "linen": [r"\blinen\b"],
    "organic wool": [r"organic\s+wool"],
    "wool": [r"\bwool\b"],
    "silk": [r"\bsilk\b"],
    "vegan leather": [r"vegan\s+leather", r"faux\s+leather", r"\bpleather\b"],
    "leather": [r"\bleather\b"],
    "cotton": [r"\bcotton\b"],
    "polyester": [r"\bpolyester\b"],
    "nylon": [r"\bnylon\b"],
}

MATERIAL_PARENT = {
    "organic cotton": "cotton",
    "recycled polyester": "polyester",
    "recycled nylon": "nylon",
    "organic wool": "wool",
    "recycled wool": "wool",
    "vegan leather": "leather",
}

# --- Certifications -------------------------------------------------------
CERTIFICATION_PATTERNS = {
    "GOTS": [r"\bgots\b", r"global organic textile standard"],
    "OEKO-TEX": [r"oeko[\s-]?tex"],
    "Fair Trade Certified": [r"fair\s?trade\s?certified", r"fairtrade\s?certified"],
    "GRS (Global Recycled Standard)": [r"global recycled standard", r"\bgrs\s?certified\b"],
    "bluesign": [r"\bbluesign\b"],
    "Cradle to Cradle": [r"cradle\s?to\s?cradle"],
    "USDA Organic": [r"usda\s?organic"],
    "B Corp": [r"\bb[\s-]?corp\b"],
}

# --- Attributes (not a material or a cert, but a meaningful, specific claim) --
ATTRIBUTE_PATTERNS = {
    "deadstock": [r"dead\s?stock"],
    "upcycled": [r"\bupcycled\b"],
    "recycled": [r"\brecycled\b"],
    "vegan": [r"\bvegan\b"],
    "handmade": [r"\bhandmade\b", r"\bhand[\s-]?made\b"],
}


def _find_matches(text: str, pattern_dict: dict) -> list:
    hits = []
    for canonical, patterns in pattern_dict.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(canonical)
                break
    return hits


def extract_signals(
    title: str = "",
    materials: str = "",
    tags: str = "",
    description: str = "",
) -> dict:
    """Scans the combined listing text and returns canonical materials,
    certifications, and specific attributes found. Empty lists mean the
    text made no specific, checkable claim -- it may still be making a
    vague sustainability claim (e.g. "eco-friendly"), which this function
    deliberately does not try to catch; that's the zero-shot layer's job."""
    combined = " ".join([title or "", materials or "", tags or "", description or ""])

    material_hits = _find_matches(combined, MATERIAL_PATTERNS)
    specific_hits = set(material_hits) & set(MATERIAL_PARENT.keys())
    parents_to_drop = {MATERIAL_PARENT[m] for m in specific_hits}
    material_hits = [m for m in material_hits if m not in parents_to_drop]

    cert_hits = _find_matches(combined, CERTIFICATION_PATTERNS)
    attribute_hits = _find_matches(combined, ATTRIBUTE_PATTERNS)

    return {
        "materials": material_hits,
        "certifications": cert_hits,
        "attributes": attribute_hits,
    }
