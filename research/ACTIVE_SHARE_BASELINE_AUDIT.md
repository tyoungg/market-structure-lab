# Active Share Baseline: First Reproducible Run Audit

**Status:** descriptive baseline successfully generated; not yet an active-only result.  
**Branch:** `RUSSEL_SP`  
**Workflow run:** [44381188999](https://github.com/tyoungg/market-structure-lab/actions/runs/44381188999)  
**Run commit:** `d257988406233c32606b90952d009c36560b9af3`

## 1. Reproducibility and source integrity

The workflow completed all steps successfully, including both source downloads, ZIP validation, TR extraction, baseline calculation, and upload of both artifacts.

| Provider | Source period | Rows | Columns | Fund IDs | Periods | Duplicate fund-period keys |
|---|---:|---:|---:|---:|---:|---:|
| Thomson Reuters (TR) | 1979-06 to 2019-12 | 831,289 | 50 | 57,980 | 163 | 0 |
| CRSP | 2020-03 to 2023-09 | 105,334 | 25 | 9,083 | 15 | 0 |

Both files had zero unparseable dates, zero missing fund identifiers, zero missing total-assets values, and zero nonpositive total-assets values. Both providers had zero duplicate full rows. The TR archive passed ZIP integrity validation.

Source-file SHA-256 values (uncompressed CSVs):

- TR: `74750db6e20e627633f018baf0bb87152b47ac5ba11e7dcac4cf9f04a1476270`
- CRSP: `bef4713891d2dabb42640d3389eed3d9dfa6d2f43523fb78b8cfe997d12d2301`

The source inventory also records the downloaded CRSP file and TR archive hashes. Raw source files remain in short-lived Actions artifacts, not in the Git repository.

## 2. What the first descriptive baseline says

The annual output reports fund-quarter observations. It calculates equal-weighted statistics across those observations and an asset-weighted mean using each quarter-observation's contemporaneous total assets. It does not first reduce each fund to one annual record.

### Thomson Reuters, 1979–2019

For S&P 500 Active Share:

- Equal-weighted mean: 89.4% in 1979 and 88.7% in 2019.
- Median: 91.8% in 1979 and 98.5% in 2019.
- Asset-weighted mean: 82.7% in 1979 and 59.2% in 2019.

For Russell 1000 Active Share:

- Equal-weighted mean: 90.5% in 1979 and 89.3% in 2019.
- Median: 92.4% in 1979 and 98.3% in 2019.
- Asset-weighted mean: 84.3% in 1979 and 60.2% in 2019.

The contrast between the median and asset-weighted mean is notable. It is consistent with assets becoming more concentrated in funds with lower measured Active Share, but this all-fund descriptive panel cannot establish that interpretation. It includes passive and other fund types and is sensitive to sample composition.

### CRSP, 2020–2023

For S&P 500 Active Share:

- Equal-weighted mean: 86.6% in 2020 and 86.6% in 2023.
- Median: 98.1% in 2020 and 98.2% in 2023.
- Asset-weighted mean: 55.8% in 2020 and 52.5% in 2023.

For Russell 1000 Active Share:

- Equal-weighted mean: 87.1% in 2020 and 87.0% in 2023.
- Median: 97.6% in 2020 and 97.8% in 2023.
- Asset-weighted mean: 57.0% in 2020 and 53.7% in 2023.

This is a short, separate CRSP window. It must not be spliced onto TR as if the provider transition were already validated.

## 3. Numerical-range checks

TR's S&P 500 and Russell 1000 Active Share fields are fully within [0, 1].

CRSP has five S&P 500 and one Russell 1000 observations slightly below zero (minimum approximately -4.1e-8). These are within the audit's 1e-6 numerical tolerance. The raw values were not clipped or rewritten. No observations exceed the tolerance bounds.

## 4. Interpretation limits

This output is a reproducible all-record descriptive baseline, not the central empirical test.

1. **No active-only classification yet.** Passive index funds, enhanced index funds, active funds, and other strategies are not separated. High Active Share does not itself establish active status, and benchmark proximity is not a valid classifier.
2. **No provider bridge yet.** TR ends in December 2019; CRSP begins in March 2020. Their levels and composition should be analyzed separately until identifiers, coverage, and methodology are reconciled.
3. **Fund-month weighting matters.** Each fund-quarter is an observation. The asset-weighted mean weights each fund-quarter by that quarter's total assets; it is not an annual cross-section or a fund-level time-series average. The output should not be described as a count of unique funds for the entire year: the `observations` field is fund-quarter rows, while `unique_funds` is the within-year distinct identifier count.
4. **Composition is unresolved.** Entry, exit, mergers, identifier changes, and changes in fund type may affect the annual distributions.
5. **This is not causal evidence.** The baseline alone cannot attribute changes to indexing, flows, performance, distribution, or trading behavior.

## 5. Next research steps

1. Complete C.1: build and validate contemporaneous fund-type classifications, retaining an explicit unclassified category and sensitivity analyses.
2. Recompute the annual baseline for active-only funds, including count and asset-weighted distributions, with 5% and 20% Active Share floors reported as separate sensitivity samples rather than definitions of active status.
3. Validate the TR-to-CRSP bridge before any combined time series.
4. Then move to C.2: construct the no-trade drift counterfactual using dated holdings, returns, benchmark weights, and corporate actions; test against both S&P 500 and Russell 1000 with style controls.

## Artifacts

The successful run uploaded:

- `active-share-source-data`: source inventory, TR archive, and CRSP source file (14-day retention).
- `active-share-baseline-outputs`: `source_audit.csv` and `annual_baseline_summary.csv` (30-day retention).

No raw source data or generated fund-level panel was committed to the repository.
