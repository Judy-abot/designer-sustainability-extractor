# Sustainability Intelligence

NLP information-extraction system that surfaces material composition,
certifications, and sustainability claims from Etsy handmade-clothing
listings and separates specific, verifiable claims from vague marketing
language.

Project 3 of 4 in a fashion-tech portfolio series, built on the same Etsy
dataset as:
- [designer-pricing-assistant](https://github.com/Judy-abot/designer-pricing-assistant) — price prediction with SHAP explainability (Project 1)
- [designer-visual-search](https://github.com/Judy-abot/designer-visual-search) — visual similarity search (Project 2)

Where Project 1 answers "what should this cost" and Project 2 answers
"what does this look like," Project 3 answers "what is this actually made
of, and is the sustainability claim specific or vague."

## How it works

A hybrid, two-layer extraction pipeline:

1. **Rule-based dictionary** (`src/material_extractor.py`): a regex-based
   gazetteer of materials (organic cotton, recycled polyester, deadstock
   fabric, vegan leather, ...) and certifications (GOTS, OEKO-TEX,
   bluesign, ...). This is the primary layer: named materials and
   certifications are a closed, enumerable vocabulary, so a dictionary
   handles the large majority of real cases without needing a model.

2. **Zero-shot classification** (`src/detect_vague_claims.py`,
   `facebook/bart-large-mnli`): scoped *only* to listings the dictionary
   found nothing in. Catches general sustainability language that doesn't
   name anything specific ("kind to our environment," "sustainable
   fashion"). Running a model on the full dataset would mostly re-confirm
   what the dictionary already settled, so it's targeted at the ambiguous
   remainder instead.

Each listing gets sorted into one of four tiers
(`src/build_sustainability_profile.py`), from most to least verifiable:

| Tier | Meaning |
|---|---|
| **Certified** | A named certification found (GOTS, etc.) |
| **Specific claim** | A specific material or attribute found (organic cotton, deadstock, vegan, ...), no formal certification |
| **Vague claim only** | A general sustainability claim, but nothing specific named — this tier doubles as the greenwashing flag |
| **No signal** | No sustainability-related text found at all |

## Results (4,500 listings)

| Tier | Count | % |
|---|---|---|
| Certified | 48 | 1.1% |
| Specific claim | 250 | 5.6% |
| Vague claim only | 118 | 2.6% |
| No signal | 4,084 | 90.8% |

**"No signal" means no textual claim was found.** The pipeline only reads what a seller wrote in the
listing; it has no way to verify anything left unstated. Most Etsy
sellers simply don't mention sustainability at all.

## App

A Streamlit app (`app.py`) to filter listings by tier and material, with
the extracted materials/certifications/attributes shown directly next to
the original listing text, so any extraction can be checked against its
source rather than trusted blindly.

## Data

Raw and processed data are not included in this repo (see `.gitignore`) —
they're fully regeneratable by running the pipeline below, starting from
Project 1's collected listings.

## Pipeline

Run in order from the project root:

```bash
python3 src/etsy_description_backfill.py   # fetch descriptions for Project 1's listings
python3 src/join_descriptions.py           # merge descriptions into the working dataset
python3 src/run_extraction.py              # run the rule-based dictionary
python3 src/diagnose_coverage.py           # optional: inspect coverage before the model step
python3 src/detect_vague_claims.py         # zero-shot layer, no-match subset only
python3 src/build_sustainability_profile.py  # build the final tiered profile
streamlit run app.py                       # browse the results
```

## Tech stack

Python · regex-based rule extraction · Hugging Face `transformers`
(zero-shot NLI, `facebook/bart-large-mnli`) · pandas · Streamlit · Etsy
Open API v3

## Limitations

- The certified tier is a small sample (n=48), any comparative claim
  built on it (e.g. a pricing premium) needs to carry that caveat rather
  than be stated as a firm result.
- English-only; listings in other languages aren't reliably caught by
  either layer.
- The material/certification dictionary was validated empirically against
  real listing text, but isn't exhaustive, some real fabric terms may
  not yet be covered.
- "No signal" reflects absence of a *textual* claim.
