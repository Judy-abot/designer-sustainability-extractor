
## 1. Zero-shot label competition skewed results toward the better-worded label

**Symptom:** on a 20-listing smoke test, 16/20 scored "True" for making a
sustainability claim given the sample was mostly floral
dresses, cosplay costumes, and tailored suits with no sustainability
language at all. One listing whose entire description was "Additional
items" scored 0.868.

**Investigation:** the classifier used two competing candidate labels,
"a sustainability or eco-friendliness claim" vs. "no sustainability
claim." The second reads as an incomplete sentence once wrapped in the
model's default hypothesis template ("This example is no sustainability
claim."), grammatically awkward next to the well-formed first option.

**Fix:** dropped the two-label competition entirely. Switched to scoring
a single label ("a sustainability or eco-friendly claim") independently
via `multi_label=True` with a 0.5 threshold, an honest yes/no question
per listing. 

**Result:** re-run on the same 20 listings, 19/20 correctly False, and
the "Additional items" listing dropped to 0.271.

## 2. A fabric swatch listing scored high on a sustainability claim it never made

**Symptom:** after the fix above, one listing — a color swatch, "Soft
Tulle Color Swatch, Over 200 Colors", still scored 0.948. Its
description was almost entirely a URL, repeated three times with
different tracking parameters.

**First hypothesis (wrong):** raw URLs are non-semantic noise a model
might not handle well. Stripped URLs from the text before classification
and re-ran.

**Result of that fix:** score barely moved, 0.948 → 0.918. URLs weren't
the actual cause.

**Actual root cause:** the listing itself is a color swatch/sample,
its own tags say "Sample|swatch|color sample." The
question "does this make a sustainability claim" doesn't meaningfully
apply to a "which color do you want" listing. Project 1's collector
already tries to exclude this kind of thing via Etsy's `is_supply` flag,
but this one slipped through, Etsy's own flag isn't fully reliable.

**Fix:** added a second, text-based filter (keyword match on title/tags
for "swatch," "color sample," "color card," and variants) and excluded
matching listings from zero-shot classification entirely.

## 3. A silent column collision in the Streamlit app's data merge

**Symptom:** would have shown missing or wrong material data in the app,
and possibly the literal string "nan" for listings with nothing
extracted.

**Root cause:** `listings_with_descriptions.csv` has a `materials` column
(the raw Etsy field, e.g. "cotton;spandex") and `sustainability_profiles.csv`
has its own, differently-meaning `materials` column (the extracted
canonical list, e.g. "organic cotton"). A naive `pandas.merge()` on
`listing_id` silently renames both to `materials_x` / `materials_y`
every reference to `row["materials"]` in the
display code would have been ambiguous or simply wrong, with no error to
flag it. Separately: an empty cell in either source file comes back from
pandas as `NaN`, not `""`, splitting that naively turns into the
literal text `"nan"`.

**Fix:** renamed the raw listings' `materials` column to `raw_materials`
before merging, and explicitly filled `NaN` with `""` on the extracted
columns right after the merge.

