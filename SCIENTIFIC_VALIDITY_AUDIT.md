# AERO-PSI scientific validity audit

**Audit date:** 2026-11-14

## Bottom line

The local archive is structurally usable and internally intact for software development. It is **not yet independently validated enough to support a claim that scientists should trust every derived result**. A scientist should trust the platform only after its source-version lineage, transformations, metric calculations, and model validation are independently reviewable.

## What passed

| Check | Result | Meaning |
|---|---|---|
| Source inventory | Pass | 180 non-system source files appear under the expected nine top-level folders. |
| Catalog integrity | Pass | Every one of the 180 catalogued files has a SHA-256 checksum; a fresh recomputation found zero mismatches. |
| Investigation provenance | Pass, internal | Eight local `i_Investigation.txt` files identify PSI-10, PSI-25, PSI-26, PSI-69, PSI-98, PSI-101, PSI-102, and PSI-159, with titles, acronyms, and NASA PSI DOIs. |
| Structured-table shape | Pass | All 10 CSV experimental tables have consistent header/row widths; no ragged records were found. |
| Catalog provenance | Pass | All 2,167 normalized experimental-condition records retain their source path and original CSV row number. |
| Source immutability | Pass at audit time | The catalog process only reads `DATA/`; it has no write path into that archive. |

## Cross-source evidence

- The local PSI-101 metadata agrees in identifier, title, DOI (`10.60555/2np7-jv14`), ISS platform, and study scope with the official NASA PSI record.
- The local SAFFIRE-I metadata agrees in identifier, title, DOI (`10.60555/0t15-1z43`), ISS platform, and study scope with the official NASA PSI record.
- The local FLEX metadata agrees in identifier, title, DOI (`10.60555/mbq8-0451`), ISS platform, and study scope with the official NASA PSI record.
- These official investigation records label those releases CC0-1.0. The project’s conservative release policy still requires a release review for each artifact it ships.

## What did not pass as a scientific-release claim

| Open issue | Why it matters | Required action |
|---|---|---|
| Exact NASA-release equivalence is unproven. | NASA PSI shows later version history for PSI-101, PSI-98, and PSI-69. File additions/removals mean a local folder cannot be called the current official mirror without a manifest comparison. | Obtain/download each official PSI version manifest or archive; record version ID/date; compare relative paths, sizes, and preferably checksums. |
| PSI-102 and the remaining five studies have not been independently checked against an official file manifest. | Local metadata is good provenance but is not a cryptographic link to the official download. | Complete the same manifest/version comparison for PSI-102, PSI-25, PSI-26, PSI-10, and PSI-159. |
| Legacy workbook semantics are not validated. | A sheet can be raw, derived, averaged, sign-inverted, or manually edited. Filename and presence do not establish scientific meaning. | Create a per-workbook import report; verify selected worksheet, time base, units, formulas/scaling, event states, and duplicate/invalid markers. |
| No raw-to-summary reproduction has been completed. | A scientist will ask whether published/compiled summary values can be recreated from selected raw runs. | Reproduce a documented number from the SAME/SAME-R final report or combined-results workbook using a frozen source run and method. |
| No model validation has been completed. | A coagulation or optical model is an assumption-driven scenario until evaluated against independent measured targets. | Compare model output to a documented size-distribution or published benchmark; report error, sensitivity, and failed cases. |
| No domain-expert review has occurred. | The archive includes ambiguous duplicates, contamination caveats, incomplete joins, and heterogeneous processing. | Ask a combustion/aerosol scientist to review the data dictionary, representative importer outputs, transformations, and final claims. |

## Scientist-trust standard for AERO-PSI

Do not use “validated,” “NASA-certified,” or “scientifically proven” in the site until all of these are true:

1. Every used investigation has an official NASA PSI version/date and manifest recorded.
2. Every used file has a source checksum and a reproducible import log.
3. Every displayed metric has a formula, units, event window, source field, and test.
4. At least one published or official summary result is independently reproduced from source data.
5. Model results are visibly distinguished from measurements and include sensitivity/limitations.
6. An independent technical reviewer can rerun the pipeline and trace a displayed result to its source.

## Safe public claims today

- “AERO-PSI catalogs a local collection of NASA PSI investigation files and preserves source-level provenance.”
- “The displayed archive inventory and CSV condition records are structurally validated.”
- “Coagulation and scattering features are planned scenario tools, not validated measurement replacements.”

## Claims to avoid today

- “This is the complete/current NASA PSI archive.”
- “The platform’s results are scientifically validated.”
- “Detector-voltage patterns prove particle size, alarm performance, or causal mechanism.”
- “Studies are quantitatively comparable across all investigations.”

