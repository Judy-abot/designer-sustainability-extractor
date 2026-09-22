# Price Premium Analysis

**Question:** does a stronger sustainability signal (from the tiered
profile) correlate with a higher listing price?

## Method

- Cross-referenced `sustainability_profiles.csv` tiers with price data
  carried through from Project 1 (`listings_with_descriptions.csv`).
- Restricted to USD-priced listings only. Price currency varies by
  seller region (`currency_code`), and mixing currencies into one
  average would be meaningless. This excludes 1,520 of 4,500 listings
  (33.8%) priced in 19 other currencies (GBP, INR, EUR, AUD, and others).
- Compared both median and mean price per tier — see below for why
  median is the number actually trusted here.

## Results (USD-only, n = 2,980)

| Tier | n | Median | Mean |
|---|---|---|---|
| Certified | 24 | $65.23 | $90.95 |
| Specific claim | 176 | $54.83 | $64.26 |
| Vague claim only | 69 | $55.00 | $72.10 |
| No signal | 2,711 | $59.99 | $109.94 |

## Why median, not mean

The "No signal" tier's mean ($109.94) is nearly double its median
($59.99) — a sign of outliers pulling the average up, not a broad price
effect across that whole tier. Checked directly rather than assumed: the
five most expensive "No signal" listings are $2,788–$4,788 archival
vintage couture pieces (MORPHEW ATELIER / MORPHEW COLLECTION), priced for
rarity and designer provenance, with nothing to do with sustainability.
A handful of listings at that price can shift a mean over 2,700+ rows
noticeably; they can't meaningfully shift a median. Mean is reported for
completeness; median is the number this analysis actually relies on.

## Finding

Certification shows a real, if modest, price association: a $65.23
median versus $54.83–$59.99 for the other three tiers. A specific,
verifiable material claim *without* formal certification does **not**
show a premium — its median ($54.83) is actually the lowest of the four
tiers, slightly below listings making no claim at all. The effect, such
as it is, appears specific to formal certification, not to sustainability
signal in general.

## Limitations

- **USD only.** 33.8% of the dataset is excluded from this comparison
  entirely; the finding may not hold across other currencies/markets.
- **Small certified sample (n = 24).** This is descriptive, not a
  statistically tested result — treat it as suggestive, not firm.
- **Correlation, not causation.** This doesn't establish that
  certification *causes* higher prices. Certified sellers may differ
  from others in ways unrelated to sustainability (established brand,
  product category mix, average listing quality) that independently
  affect price.
