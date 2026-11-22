# C.1 Manual Adjudication — Prospectus Candidates and N-SAR Item 69

**Branch:** `RUSSEL_SP`  
**Decision register:** [`c1_manual_adjudications.csv`](c1_manual_adjudications.csv)  
**Scope:** Five automated prospectus candidates and all nine Item 69-positive fund-years in the bounded 80-CIK sample.

## Executive decisions

- **Nine fund-years confirmed as `passive_index`**: three SEC series, each observed in 2007, 2008, and 2009.
- **No active fund-year promoted.** The five prospectus candidates are either false positives, plausible active strategies filed too late for the panel, or an enhanced-index-like strategy filed too late.
- **181 Item 69 N fund-years remain unclassified.** An N response means “not reported as an index fund”; it is not evidence of active management.
- **No active-only panel is validated.** This review improves the passive-index labels but does not solve the much larger active/unclassified coverage problem.

## 1. Item 69 positive fund-years

The three series were reviewed against the contemporaneous SEC submission header, Item 007 series name, and Item 69 response in the original `answer.fil` document. The series ID/name in the SEC header and the Item 007 name agree for each series. The original six-character coordinates are preserved by the corrected extractor and checked against the actual filings.

| Fundno | Series | 2007 evidence | 2008 evidence | 2009 evidence | Decision |
|---:|---|---|---|---|---|
| 65260 | LargeCap S&P 500 Index Fund (S000007016) | 2006-12-29 / 2006-10-31 / `001400=Y` | 2007-12-28 / 2007-10-31 / `001400=Y` | 2008-12-30 / 2008-10-31 / `001400=Y` | `passive_index` |
| 64887 | MidCap S&P 400 Index Fund (S000007079) | 2006-12-29 / 2006-10-31 / `002400=Y` | 2007-12-28 / 2007-10-31 / `002400=Y` | 2008-12-30 / 2008-10-31 / `002400=Y` | `passive_index` |
| 6634 | SmallCap S&P 600 Index Fund (S000007203) | 2006-12-29 / 2006-10-31 / `004100=Y` | 2007-12-28 / 2007-10-31 / `004100=Y` | 2008-12-30 / 2008-10-31 / `004100=Y` | `passive_index` |

All nine filing/report pairs meet the predeclared as-of rule: filing date and report date precede January 1 of the fund-year, and the report period is within 548 days of the cutoff. Each positive is a series-level response, not a registrant-level answer.

### Primary-source checks

The SEC filings below are the source documents from which the coordinates were checked:

- [2006 N-SAR-B, accession 0001325358-06-000577](https://www.sec.gov/Archives/edgar/data/898745/000132535806000577/0001325358-06-000577.txt): Item 69 responses at `001400`, `002400`, and `004100` are Y.
- [2007 N-SAR-B, accession 0001325358-07-000557](https://www.sec.gov/Archives/edgar/data/898745/000132535807000557/0001325358-07-000557.txt): the same three coordinates are Y.
- [2008 N-SAR-B, accession 0001325358-08-000661](https://www.sec.gov/Archives/edgar/data/898745/000132535808000661/0001325358-08-000661.txt): the same three coordinates are Y.

The coordinate distinction matters. For example, the SmallCap S&P 600 Index Fund is coordinate `004100`, not the nearby `002500` coordinate. In the 2008 filing, `069 004100 Y` is present in the series block; `069 002500` belongs to a different series and is N. The extractor must preserve the full coordinate rather than infer it from ordinal or nearby text.

### Identity and share-class limitation

The fund-year ledger's series link is unique for each of these nine rows, and the SEC historical header/Item 007 identities agree. The ledger also marks the rows `share_class_ambiguous=true` because the registry contains multiple class contracts for each series. The adjudication is therefore at the **portfolio-series level**. It does not claim that a particular share class was uniquely identified, and the ambiguity flag remains in the ledger.

## 2. Prospectus candidate dispositions

The five phrase-extractor candidates were manually reviewed against the series-specific text and timing:

| Series | Strategy disposition | Panel eligible? | Reason |
|---|---|---:|---|
| Small Cap Growth (S000008810) | Rejected false positive; unclassified | No | Trigger phrase is boilerplate. Extracted passage begins with Security Large Cap Value Fund and describes a different fund's Russell 1000 Value strategy. |
| Fidelity Advisor Value Fund (S000017687) | Active value strategy at filing date | No | FMR's series-specific principal strategy describes bottom-up fundamental analysis and selection of undervalued companies. Filing is 2009-12-29, after the panel's final observation and after the 2009-01-01 cutoff. |
| Fidelity Advisor Value Leaders Fund (S000005435) | Active value strategy at filing date | No | Series-specific text describes blue-chip selection, fundamental valuation, and bottom-up analysis. Filing is 2009-12-29, after the panel's final observation and after the 2009-01-01 cutoff. |
| Eagle Growth & Income Fund (S000008475) | Unclassified; series-context mismatch | No | Extracted strategy section is headed Capital Appreciation Fund, not the matched Eagle Growth & Income series. |
| Dreyfus Structured Midcap Fund (S000000499) | Enhanced-index-like candidate | No | At least 80% of assets are constrained to S&P 400 or Russell Midcap constituents; a quantitative valuation/momentum/quality process makes benchmark-aware overweight/underweight decisions. Filing is 2009-12-23, after the observed period. |

The two Fidelity filings are plausible evidence of active value strategies as of their filing dates, but they cannot be backdated into the observed panel. Dreyfus is retained as an enhanced-index-like candidate rather than mislabeled as conventional active. Small Cap Growth and Eagle are not accepted as series-specific evidence.

## 3. Ledger implementation and acceptance

The builder consumes the manual register and enforces the following checks before promoting a fund-year to `passive_index`:

1. Exact match on `fundno_key`, fund-year, CIK, and SEC series ID.
2. Recomputed as-of status is Item 69 Y and the latest eligible response is Y.
3. Manual accession matches the latest eligible accession in the ledger.
4. Manual response is Y, the coordinate is present, and the adjudicated class is `passive_index`.
5. Duplicate manual decisions for a fund-year are rejected.

The corrected extraction artifact contains all 409 series-level evidence rows with `item69_coordinate` and `all_item69_coordinates`. The nine adjudications above are the only fund-years promoted. Item 69 N is never converted to active.

## 4. C.1 implication

The bounded N-SAR sample now provides a small set of defensible passive-index exclusions: nine fund-years across three series. It does not provide positive active evidence. The five prospectus candidates produce no in-sample active labels under the strict time cutoff. The remaining 22,271 fund-years in the 22,280-row ledger remain unclassified unless supported by additional contemporaneous evidence.

**Decision:** retain the nine passive-index classifications; do not construct or publish an active-only panel from the current evidence. Continue with effective-date retrieval and predeclared prospectus-staleness sensitivity analysis, then make an explicit C.1 go/no-go decision.
