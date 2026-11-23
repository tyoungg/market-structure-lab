# C.1 Predecessor/Successor Series Recovery Audit

**Branch:** \`RUSSEL_SP\`  
**Scope:** Notre Dame/TR fundno 53752 (Everest / Calvert), plus a mechanical identity-discontinuity screen of the existing fund-year ledger.  
**Source ledger:** [run 45028704608](https://github.com/tyoungg/market-structure-lab/actions/runs/45028704608), artifact \`fund-year-evidence-ledger\` (ID 14757095448).

## Result

The Everest/Calvert case confirms a real predecessor/successor identity failure in the C.1 panel.

- The current ledger has no strict SEC series candidate for fundno 53752 in 2000–2007.
- It first maps the fundno to Calvert Large Cap Value, successor series S000023592, in 2008.
- The 2007 row is unclassified even though the February 1, 2006 Everest prospectus is pre-cutoff and describes active value selection.
- The 2008 row is unclassified because the Calvert prospectus evidence currently linked to it is post-cutoff. The February 1, 2007 Everest prospectus is valid as-of evidence for 2008 but was missed because the predecessor series was not in the later registry bridge.
- The 2009 Calvert Large Cap Value row is already included in the original 30 active adjudications.

**Recovery disposition:** two additional active fund-year lineage observations are supported: 2007 (Everest predecessor) and 2008 (Everest-to-Calvert transition year). The potential seed becomes 32 active fund-years across 15 legal SEC series, pending integration into the canonical builder. This does not change the C.1 no-go for population-level inference.

## SEC evidence chain

1. **Predecessor strategy.** The February 1, 2006 Summit prospectus describes Everest Fund as primarily invested in common stocks and seeking undervalued securities using a value strategy. The February 1, 2007 prospectus repeats this active value approach.  
   Sources: [2006 prospectus](https://www.sec.gov/Archives/edgar/data/743773/000074377306000003/epea206.txt), [2007 prospectus](https://www.sec.gov/Archives/edgar/data/743773/000074377307000006/apex485b.txt).

2. **Predecessor series identity.** The February 1, 2007 SEC submission header identifies Everest Fund as CIK 0000743773, series S000010985, with Class I C000030360 / SAEVX and Class A C000030361 / SEVRX. For the 2007 fund-year, that header is a later cross-reference only; it is not treated as evidence available at the January 1, 2007 cutoff. The 2006 prospectus itself supplies the pre-cutoff Everest fund-name and strategy evidence. For the 2008 cutoff, the 2007 header is contemporaneous and pre-cutoff.  
   Source: [SEC submission header, accession 0000743773-07-000006](https://www.sec.gov/Archives/edgar/data/743773/000074377307000006/0000743773-07-000006.txt).

3. **Successor strategy and transition.** Calvert's November 4, 2008 prospectus describes a fundamentally selected portfolio of undervalued large-cap U.S. companies. The October 31, 2008 proxy identifies Summit Everest as merging into Calvert Large Cap Value. Calvert's March 31, 2009 shareholder report confirms that the asset transfer and Everest share liquidation occurred on December 12, 2008.  
   Sources: [Calvert prospectus](https://www.sec.gov/Archives/edgar/data/1438390/000143839008000018/csf485bfiled110408.htm), [reorganization proxy](https://www.sec.gov/Archives/edgar/data/1438390/000143839008000015/csfn14afiled103008.htm), [Calvert N-CSR confirming the effective date and liquidation](https://www.sec.gov/Archives/edgar/data/1438390/000143839009000007/csfncsrsfiled060509.htm).

The N-CSR says Everest was the accounting survivor for financial-reporting purposes. That explains linked historical performance under Calvert's later history; it does not mean the Calvert legal series ID existed before December 12, 2008.

## Fund-year disposition

| Fund-year | Current ledger | Recovered treatment |
|---|---|---|
| 2007 | No strict series candidate; unclassified | Recover as active value predecessor lineage, using the pre-cutoff February 1, 2006 Everest prospectus |
| 2008 | Four period records mapped to Calvert successor; no pre-cutoff prospectus linked; unclassified | Recover as active value lineage with \`transition_mixed_series\`; split identity by actual quarter-end date at December 12 |
| 2009 | Calvert successor; already active in original 30 | Retain existing adjudication; no double count |

The Notre Dame Thomson Reuters data are end-of-quarter observations. The 2008 annual row spans the December 12 legal transition and must not be assigned wholly to either series. Preserve each holdings report date and do not carry successor S000023592 backward over pre-merger snapshots.

The same registrant reorganization also transferred Summit Bond Fund to Calvert Income and Summit Money Market Fund to Calvert Institutional Prime. Those are genuine additional legal transitions, but they do not add U.S. equity observations to this Active Share panel. Other Summit portfolios continued under Calvert management rather than merging; an adviser change alone is not a predecessor/successor series event.

## Is this recurring?

**One confirmed in-panel recovery** was found in this bounded review: Everest → Calvert Large Cap Value. It contributes one clean predecessor year (2007) and one mixed transition year (2008); the successor year (2009) was already counted.

A mechanical screen of the 22,280-row ledger found **64 fundnos** whose first unique-series match occurs in 2007–2009 after one or more earlier no-strict-candidate years. These cases contain 565 earlier no-strict fund-years and 123 later unique-series fund-years. Fundno 53752 is one of the 64.

This is a review queue, **not** 64 proven mergers or 64 missed active funds. The same pattern can arise from delayed series-ID issuance, name/ticker mismatches, incomplete historical registry coverage, reused Thomson Reuters fundnos, or genuine reorganizations. A broader screen finds 382 fundnos with a no-strict year followed later by a unique-series year somewhere in 1980–2009; that larger count is even less specific.

The SEC's downloadable Series and Class Report begins in January 2010, while electronic series/class IDs became required for open-end mutual fund filings beginning February 6, 2006. A later registry snapshot is not a complete historical register of predecessor series that had already merged or ceased operation. A terminated predecessor can disappear from the bridge while its holdings history remains in the TR panel.  
Source: [SEC Investment Company Series and Class Information](https://www.sec.gov/data-research/sec-markets-data/investment-company-series-class-information).

## Integration rules and C.1 conclusion

1. Preserve predecessor and successor IDs, CIKs, effective dates, class IDs/tickers, and source accessions in an explicit lineage layer.
2. Do not backdate Calvert S000023592. Pre-December 12, 2008 holdings belong to Everest S000010985.
3. Integrate 2007 and 2008 only through a lineage-aware build; preserve 2008 as a mixed-series transition year and rerun tests before changing canonical counts.
4. Keep the 64 identity-discontinuity cases unclassified until individually reviewed.
5. Even at 32 active fund-years, C.1 remains no-go for population-level active-only inference. The additions are one value-oriented lineage, still concentrated in 2007–2009, with no active large-cap core observation.

## Reproducible outputs

- \`C1_PREDECESSOR_SUCCESSOR_RECOVERIES.csv\` — the two proposed lineage recoveries and their identity/strategy dispositions.
- \`C1_SERIES_IDENTITY_DISCONTINUITY_SCREEN.csv\` — 64 unreviewed identity-discontinuity candidates; none is promoted by the screen alone.
- Source ledger: run 45028704608, artifact 14757095448.
