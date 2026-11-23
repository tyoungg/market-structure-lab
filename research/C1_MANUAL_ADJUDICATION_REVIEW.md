# C.1 Manual Adjudication — Prospectus and N-SAR Evidence

**Branch:** `RUSSEL_SP`  
**Decision register:** [`c1_manual_adjudications.csv`](c1_manual_adjudications.csv)  
**Bounded source scope:** 80 CIKs; 191 target SEC series; 22,280 fund-year rows.

## Executive result

- **30 active fund-years** are manually confirmed from contemporaneous, series-linked prospectuses, covering 14 series in 2007–2009.
- **Nine passive-index fund-years** are manually confirmed from series-specific N-SAR Item 69 Y responses, covering three series in 2007–2009.
- **22,241 fund-years remain unclassified.** The 181 Item 69 N rows are not active evidence.
- The active evidence is only 30 of 22,280 fund-year rows (0.135%), clustered in the last three years. It is not a representative historical active-only panel.
- The five automated phrase-extractor candidates are separately adjudicated; none adds an in-panel active row because their filings are too late or the series context is invalid.

## 1. Direct review of all as-of prospectus evidence

The ledger contains 30 as-of prospectus fund-year/evidence links across 14 distinct series. The automated phrase/context extractor marked these links unclassified, so each primary prospectus was reviewed directly. The review confirmed discretionary security selection, fundamental or quantitative research, and manager-set portfolio weights. Index references in several prospectuses define a market-cap universe or performance comparator; they do not describe index replication.

| Series | Fundno | Fund-years | Original evidence filing date | Manual strategy decision |
|---|---:|---|---|---|
| Dreyfus S&P STARS Fund | 1366 | 2008–2009 | 2007-07-27 | Active stock selection based on S&P STARS analyst ratings |
| Dreyfus S&P STARS Opportunities Fund | 64960 | 2008–2009 | 2007-07-27 | Active STARS selection and shorting strategy |
| Legg Mason Capital Management Opportunity Trust | 52926 | 2007–2009 | 2006-09-15 | Flexible, unconstrained active security and asset selection |
| Baird LargeCap Fund | 60020 | 2007–2009 | 2006-04-27 | Active fundamental and quantitative stock selection |
| Baird MidCap Fund | 60021 | 2007–2009 | 2006-04-27 | Active fundamental and quantitative stock selection |
| Baird SmallCap Fund | 45178 | 2007 | 2006-04-27 | Active fundamental and quantitative stock selection |
| Touchstone Sands Capital Institutional Growth Fund | 48042 | 2008–2009 | 2007-05-01 | Active concentrated growth selection by Sands Capital |
| Morgan Stanley Mid Cap Value Fund | 67019 | 2008 | 2006-12-11 | Active mid-cap value selection |
| Optimum Large Cap Growth Fund | 38997 | 2008–2009 | 2007-07-27 | Active multi-subadviser growth selection |
| Optimum Small-Mid Cap Growth Fund | 38964 | 2008–2009 | 2007-07-27 | Active subadviser growth selection; name/universe change effective 2008-01-01 |
| Optimum Small-Mid Cap Value Fund | 39005 | 2008–2009 | 2007-07-27 | Active subadviser value selection; name/universe change effective 2008-01-01 |
| Fort Pitt Capital Total Return Fund | 71760 | 2007–2009 | 2006-02-24 | Active fundamental stock selection and flexible equity/fixed-income allocation |
| The Hillman Focused Advantage Fund | 81148 | 2007–2009 | 2006-05-09 | Active focused portfolio selected using qualitative and quantitative company analysis |
| Calvert Large Cap Value Fund | 53752 | 2009 | 2008-11-04 | Active bottom-up fundamental value selection with responsibility screens |

All 30 rows are adjudicated `other_active_style`. No row is assigned to `active_large_cap_core`: these are growth, value, focused, flexible, total-return, or systematic active strategies rather than a clean large-cap core category.

### Important source-specific decisions

**Baird SmallCap context correction.** The automated context snippet attached to Baird SmallCap began with the LargeCap section, so the snippet itself was rejected. The complete May 1, 2006 prospectus has separate LargeCap, MidCap, and SmallCap strategy sections. The SmallCap section independently describes discretionary quantitative/fundamental security selection. Baird SmallCap is therefore confirmed active for its single as-of 2007 fund-year; the extractor's context assignment, not the series, was wrong.

**Optimum small/mid name change.** The July 2007 prospectus uses the former names Optimum Small Cap Growth Fund and Optimum Small Cap Value Fund. A later SEC prospectus identifies the new Small-Mid names as former names and states that the investment universe changed effective January 1, 2008. That later document is used only to resolve the name transition; the contemporaneous 2007 prospectus supplies the active strategy evidence. The two series remain active after the change because their sub-advisers continue using their respective investment styles and strategies.

**Near-name aliases.** The Dreyfus prospectuses use the “Premier” prefix; Legg Mason's prospectus omits “Capital Management”; and the Touchstone filing names the portfolio as “CIP Sands Capital Institutional Growth Portfolio.” The target SEC series IDs are present in the corresponding submission headers, and each fund/portfolio name and strategy has a unique one-to-one match within the filing. These aliases are explicitly documented in the decision register rather than silently normalized.

**Benchmark references are not index mandates.** Baird, Morgan Stanley, Calvert, and Optimum use S&P or Russell indexes to define market-cap ranges or compare performance. Their prospectuses describe adviser security selection, fundamental/quantitative research, and discretionary portfolio decisions. They are classified active, not passive or enhanced-index, on that basis.

### Timing and effective-date notes

- Fort Pitt's filing states effectiveness on February 28, 2006.
- Baird's prospectus is dated May 1, 2006; its filing was submitted April 27, 2006.
- Hillman's filing states effectiveness 60 days after May 9, 2006, before the first included 2007 cutoff.
- Legg Mason's filing is effective September 15, 2006.
- Morgan Stanley's filing is dated December 11, 2006; the prospectus is dated December 29, 2006. No separate new effective date is stated on the cover; the filing and prospectus dates both precede the 2008 cutoff used for its observed row.
- Touchstone's prospectus is dated May 1, 2007.
- Optimum's prospectus is dated July 29, 2007; the small/mid strategy/name change is effective January 1, 2008.
- Dreyfus's 2007 prospectus is filed July 27, 2007 and identifies the two STARS funds.
- Calvert's November 4, 2008 filing is marked effective immediately and incorporates the October 31, 2008 prospectus; the fund commenced operations December 12, 2008. The later 497 prospectus filed December 9, 2008 (dated December 12) documents the Everest Fund reorganization and is the latest as-of base prospectus for the 2009 row.

Where an explicit effective date is not stated, the register retains the filing/prospectus date and does not invent an effective date.

## 2. Automated prospectus phrase-candidate dispositions

The five automated active phrase candidates were reviewed separately:

| Series | Manual disposition | In-panel? | Reason |
|---|---|---:|---|
| Small Cap Growth (S000008810) | Rejected false positive | No | Extracted context describes Security Large Cap Value Fund, not the matched Small Cap Growth series |
| Fidelity Advisor Value Fund (S000017687) | Active value strategy at filing date | No | Series-specific fundamental bottom-up value strategy; filing dated 2009-12-29, after the panel cutoff and final observation |
| Fidelity Advisor Value Leaders Fund (S000005435) | Active value strategy at filing date | No | Series-specific fundamental/blue-chip value strategy; filing dated 2009-12-29, after the panel cutoff and final observation |
| Eagle Growth & Income Fund (S000008475) | Unclassified identity/context mismatch | No | Extracted strategy passage is headed Capital Appreciation Fund |
| Dreyfus Structured Midcap Fund (S000000499) | Enhanced-index-like candidate | No | Benchmark-constituent constraint and quantitative benchmark-aware overweight/underweight process; filing is post-sample |

These five decisions do not add fund-year classifications to the 1980–2009 observed panel.

## 3. N-SAR Item 69 positive adjudications

The three series below were checked against the SEC submission header, Item 007 series name, and the original Item 69 response coordinate. Each of the three filings has a Y at the stated coordinate.

| Fundno | Series | 2007 evidence | 2008 evidence | 2009 evidence |
|---:|---|---|---|---|
| 65260 | LargeCap S&P 500 Index Fund (S000007016) | 2006-12-29; report 2006-10-31; `001400=Y` | 2007-12-28; report 2007-10-31; `001400=Y` | 2008-12-30; report 2008-10-31; `001400=Y` |
| 64887 | MidCap S&P 400 Index Fund (S000007079) | 2006-12-29; report 2006-10-31; `002400=Y` | 2007-12-28; report 2007-10-31; `002400=Y` | 2008-12-30; report 2008-10-31; `002400=Y` |
| 6634 | SmallCap S&P 600 Index Fund (S000007203) | 2006-12-29; report 2006-10-31; `004100=Y` | 2007-12-28; report 2007-10-31; `004100=Y` | 2008-12-30; report 2008-10-31; `004100=Y` |

The original six-character coordinates are preserved in all 409 source evidence rows. The SmallCap S&P 600 response is `004100`; the nearby `002500` coordinate belongs to a different series and is N. The as-of rule is unchanged: filing and report dates must precede January 1 of the fund-year and the report must be no more than 548 days old.

The ledger continues to retain `share_class_ambiguous=true` for these funds. The adjudication is at the portfolio-series level, not a claim that one share class was uniquely identified.

Primary SEC filings:
- [2006 N-SAR-B, accession 0001325358-06-000577](https://www.sec.gov/Archives/edgar/data/898745/000132535806000577/0001325358-06-000577.txt)
- [2007 N-SAR-B, accession 0001325358-07-000557](https://www.sec.gov/Archives/edgar/data/898745/000132535807000557/0001325358-07-000557.txt)
- [2008 N-SAR-B, accession 0001325358-08-000661](https://www.sec.gov/Archives/edgar/data/898745/000132535808000661/0001325358-08-000661.txt)

## 4. Original selected-source prospectus-age sensitivity

The table below reports the age of the **original selected evidence links** in the adjudication register. It is not the age of the latest available as-of prospectus. The independent full-history audit found a later applicable base prospectus for every fund-year: **30/30 were filed within 365 days** of the January 1 cutoff. See [Independent C.1 audit of the 30 adjudications](C1_ACTIVE30_INDEPENDENT_AUDIT.md).

The no-expiry rule remains the primary evidence ledger. The 1-, 2-, and 3-year windows below are sensitivity filters applied to the original selected source links after manual strategy adjudication; they do not create a strategy class.

| Maximum filing age | Prospectus fund-year links retained | Manually confirmed active links |
|---|---:|---:|
| 365 days | 13 | 13 |
| 730 days | 25 | 25 |
| 1,095 days | 30 | 30 |
| No expiry | 30 | 30 |

The 1-year and 2-year filters reduce the active sample substantially. The 3-year and no-expiry results coincide because the oldest as-of prospectus evidence in this bounded set is 1,042 days old. No evidence is backdated: each fund-year link still requires a filing before its January 1 cutoff.

## 5. C.1 implication

The independent filing-history audit upheld all 30 active labels, found 14/14 target series and 30/30 name-matched as-of document candidates, and identified newer base prospectuses within 365 days for all 30 fund-years. It also identified a Calvert/Everest predecessor-series recovery candidate; that candidate is not yet added to the adjudicated register. See [the independent audit report](C1_ACTIVE30_INDEPENDENT_AUDIT.md).

The evidence ledger now has 30 active fund-years, nine passive-index fund-years, and 22,241 unclassified fund-years. The 30 active rows represent 14 funds but are concentrated entirely in 2007–2009. They are a useful manually validated seed set for diagnostics, not a representative active-only historical panel.

**Decision:** do not publish or use the current 30-row subset as a general active-only panel. Preserve the manually adjudicated labels, report the staleness sensitivities, and continue only if broader contemporaneous series-specific coverage can be established. Item 69 N remains unclassified; it is never promoted to active.
