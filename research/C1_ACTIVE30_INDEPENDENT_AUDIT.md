# Independent C.1 Audit of the 30 Adjudicated Active Fund-Years

**Branch:** `RUSSEL_SP`  
**Population:** 30 existing active fund-year adjudications, 14 SEC series, nine registrants, 2007–2009  
**Audit run:** [C.1 independent EDGAR history audit, run #2](https://github.com/tyoungg/market-structure-lab/actions/runs/45261305364)  
**Artifact:** `c1-active30-independent-filing-history`, artifact ID `14860298577`  
**Protocol and retrieval code:** [audit protocol](C1_ACTIVE30_INDEPENDENT_AUDIT_PROTOCOL.md), [retrieval script](../scripts/audit_c1_active30_filing_history.py)

## Executive result

**All 30 original active classifications remain supported.** The independent review found no passive-index or enhanced-index strategy among these 30 observations. All 30 remain `other_active_style`; none qualifies as `active_large_cap_core`.

The new filing-history search materially improves the source record:

- 30/30 fund-years have at least one **name-matched** pre-cutoff candidate document.
- 14/14 target SEC series were found; all 14 original adjudication accessions were found.
- The scan covered 238 relevant filings and downloaded 245 documents, producing 295 series/document links and 509 fund-year/document links.
- 67 header-only links were not accepted as strategy evidence. A series ID in a filing header is an identity clue, not proof that every attached document applies to that series.
- The 23/30 rows marked `share_class_ambiguous` in the older crosswalk have multiple class IDs **within one unique matched series**. They do not have multiple competing series matches. The field should be read as a share-class-count warning, not an unresolved portfolio identity.
- After reviewing the latest applicable base prospectus for each fund-year, all 30 were filed within 365 days of the January 1 as-of cutoff. The age range is 11–332 days.

The workflow's strict validation step did **not** pass: three SEC retrieval errors were recorded. Two relevant documents were recovered through direct SEC access; the third was an older 2005 Baird submission superseded by the 2006 prospectus used for the 2007 observation. The artifact was preserved, and no evidence was inferred from failed downloads. The automatic `document_kind` field is a heuristic: 497J no-change certifications and prospectus/SAI stickers require review of the filing form, description, and document text. The latest-prospectus dates below are the manually reviewed result, not a blind use of that heuristic.

## Latest as-of base prospectus review

Age is calculated as January 1 of the fund-year minus the SEC filing date. Where one prospectus covers multiple series, the same filing is listed for each applicable fund.

| Fund / series | Fund-years | Latest applicable base prospectus filing date and age |
|---|---|---|
| Dreyfus S&P STARS Fund | 2008, 2009 | 2007-09-14 (109 days); 2008-07-29 (156 days) |
| Dreyfus S&P STARS Opportunities Fund | 2008, 2009 | 2007-09-14 (109 days); 2008-07-29 (156 days) |
| Legg Mason Capital Management Opportunity Trust | 2007, 2008, 2009 | 2006-09-15 (108 days); 2007-04-27 (249 days); 2008-12-08 (24 days) |
| Baird LargeCap Fund | 2007, 2008, 2009 | 2006-05-03 (243 days); 2007-04-27 (249 days); 2008-04-30 (246 days) |
| Baird MidCap Fund | 2007, 2008, 2009 | 2006-05-03 (243 days); 2007-04-27 (249 days); 2008-04-30 (246 days) |
| Baird SmallCap Fund | 2007 | 2006-05-03 (243 days) |
| Touchstone Sands Capital Institutional Growth Fund | 2008, 2009 | 2007-11-26 (36 days); 2008-05-01 (245 days) |
| Morgan Stanley Mid Cap Value Fund | 2008 | 2007-12-21 (11 days) |
| Optimum Large Cap Growth Fund | 2008, 2009 | 2007-07-27 (158 days); 2008-07-28 (157 days) |
| Optimum Small-Mid Cap Growth Fund | 2008, 2009 | 2007-07-27 (158 days); 2008-07-28 (157 days) |
| Optimum Small-Mid Cap Value Fund | 2008, 2009 | 2007-07-27 (158 days); 2008-07-28 (157 days) |
| Fort Pitt Capital Total Return Fund | 2007, 2008, 2009 | 2006-03-03 (304 days); 2007-02-28 (307 days); 2008-02-29 (307 days) |
| The Hillman Focused Advantage Fund | 2007, 2008, 2009 | 2006-07-13 (172 days); 2007-02-05 (330 days); 2008-02-04 (332 days) |
| Calvert Large Cap Value Fund | 2009 | 2008-12-09 (23 days) |

The two relevant documents that failed automated retrieval were independently opened from SEC EDGAR:

- [Fort Pitt 2008 post-effective prospectus, filed February 29, 2008](https://www.sec.gov/Archives/edgar/data/1158727/000089418908000757/fortpitt_485b.htm)
- [Touchstone 2008 post-effective prospectus, filed May 1, 2008](https://www.sec.gov/Archives/edgar/data/1174490/000114420408025355/v111613_485bpos.txt)

The remaining failed request was for an older 2005 Baird submission. It predates the May 2006 Baird prospectus used for the 2007 fund-year and does not change any of the 30 as-of decisions.

### Interpreting the prior staleness table

The earlier 13/25/30 result measured the age of the **initially selected evidence links** in the adjudication ledger. It did not measure the age of the latest available as-of prospectus. The independent full-history review finds 30/30 latest base prospectuses within 365 days. The original sensitivity output remains reproducible for its original source links, but it must not be presented as evidence that only 13 of the 30 funds had a recent prospectus available.

## Classification and structural findings

The prospectuses describe discretionary security selection, adviser/sub-adviser research, and manager-set portfolio weights. Index references define a market-cap universe or performance comparator; they do not make these funds index trackers. The strategy classes remain:

- **30 active / other active-style**
- **0 active large-cap core**
- **0 passive or enhanced-index among these 30**

The following changes matter for interpreting the fund-year observations, but none converts an active strategy into a passive one:

1. **Dreyfus S&P STARS Fund:** the April 2008 supplement removed Bear Stearns Asset Management as sub-adviser and returned day-to-day management to Dreyfus/TBCAM. The 2009 annual report records a primary portfolio-manager designation change effective January 6, 2009, after the January 1 as-of cutoff. Class T ticker BSPAX and later Class A ticker DPPAX are different classes of the same series; the class conversion was effective in February 2009.

2. **Dreyfus S&P STARS Opportunities Fund:** the fund name dropped the “Premier” prefix in December 2008. It absorbed Dreyfus Premier Midcap Stock Fund effective December 17, 2008. This is a material portfolio reorganization before the 2009 cutoff, not a change to passive management.

3. **Legg Mason Opportunity Trust:** the December 2008 prospectus remains a flexible, actively managed strategy. An August 2008 supplement added an assistant portfolio manager; it did not turn the fund into an index strategy.

4. **Baird MidCap Fund:** 2008 supplements document portfolio-manager roster changes, including Carla Cooper's appointment in August 2008. The fund remained actively managed. The August 2008 Baird SmallCap sticker applies to the SmallCap Fund, not LargeCap or MidCap.

5. **Baird SmallCap Fund:** its 2007 active classification is valid as of January 1, 2007. A later 2008 supplement announced liquidation effective October 31, 2008; that explains why no later Baird SmallCap fund-year appears in the 30-row set.

6. **Touchstone Sands Capital Institutional Growth Fund:** the trust and fund names changed from the CIP names to Touchstone names, while Sands Capital remained the sub-adviser. The May 2008 SAI explicitly refers to the May 1 prospectus and an 80% policy investing in U.S. common stocks with above-average revenue and earnings growth. This is active growth, not index replication.

7. **Optimum Small-Mid Growth and Value Funds:** the former Small Cap names and investment universes changed to Small-Mid effective January 1, 2008, with the benchmark moving from Russell 2000 to Russell 2500. Wellington became sub-adviser to Growth effective June 25, 2008; Westwood replaced H&W for Value effective December 17, 2008. Both remain active style strategies.

8. **Optimum Large Cap Growth Fund:** Marsico's prior sub-advisory agreement terminated after a change in Marsico control, and a new agreement became effective December 14, 2007. Marsico remained the sub-adviser; the new terms were substantially similar and the Board was told no portfolio-management personnel changes were planned. This is an agreement/control event, not evidence of a switch to passive management.

9. **Hillman Focused Advantage Fund:** the December 2008 supplement changes the custodian; it does not change the investment strategy.

10. **Fort Pitt Capital Total Return Fund:** the 2008 prospectus continues to describe discretionary stock selection and flexible equity/fixed-income allocation. “Buy and hold” is not synonymous with passive index management.

11. **Calvert Large Cap Value Fund:** the 2009 observation is a successor-series observation after the Everest Fund reorganization described below.

## Identity and predecessor/successor recovery

The 2010 SEC series/class crosswalk's `share_class_ambiguous` flag is not evidence of multiple portfolio series. For all 30 adjudicated fund-years, the strict candidate set resolves to one SEC series. Multiple class IDs within that series represent share classes of the same portfolio. Dreyfus Class T/Class A and Legg Mason share-class changes should therefore be kept separate from series identity.

**Calvert/Everest is a genuine series transition.** The 2008 SEC filing index identifies the predecessor Everest Fund as CIK 743773, series `S000010985`, Class I `C000030360`, ticker `SAEVX`. The December 12, 2008 Calvert prospectus says the Everest Fund's Class A and Class I assets were reorganized into Calvert Large Cap Value's Class A and Class Y shares. The successor Calvert series is `S000023592`. The Calvert Class Y performance history before December 12, 2008 reflects the predecessor Everest Fund; it is not evidence that the Calvert legal series was operating throughout those earlier quarters.

Sources: [Everest SEC series/class filing index](https://www.sec.gov/Archives/edgar/data/743773/000074377308000005/0000743773-08-000005-index.html), [Calvert December 12, 2008 prospectus](https://www.sec.gov/Archives/edgar/data/1438390/000143839008000021/csf497efiled120808.htm).

This creates a **recovery candidate**, not an automatic addition to the 30: Notre Dame `fundno 53752` has predecessor Everest observations in 2007 and a mixed predecessor/successor lineage during 2008. The 2006 and 2007 Everest prospectuses describe an active value strategy. Before promoting additional fund-years, separately verify the historical predecessor series header and the 2007/2008 as-of filings, and split the 2008 lineage at December 12. Do not silently treat the successor SEC series as if it existed before that date.

## C.1 decision

The 30 active classifications are supported, and the as-of source record is materially stronger than the original bounded filing selection suggested. But the population-level C.1 gate remains **no-go**:

- 30 active fund-years are only 0.135% of the 22,280-row panel.
- They represent 14 series, all in 2007–2009.
- No active large-cap core fund-year is present.
- The 181 Item 69 N responses remain unclassified; N is not active evidence.
- The 30 observations cannot support a historical active-only trend or a claim about established core managers generally.

The next C.1 task is targeted predecessor/successor recovery and broader series-specific historical coverage, not another pass over the same 30 documents. Preserve the 30 as a validated positive seed set; do not use it as a representative active-only panel.
