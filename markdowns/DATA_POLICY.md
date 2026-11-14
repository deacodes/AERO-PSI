# AERO-PSI source-data policy

## Decision for this project

1. `DATA/` is a local, read-only source archive and is excluded from Git by default.
2. The public project may include code, schemas, source-relative paths, transformation logic, non-sensitive aggregate metrics, and screenshots with clear provenance.
3. Do **not** upload, bundle, mirror, or redistribute original NASA spreadsheets, documents, images, or raw source-derived files until their applicable source terms and publication status have been reviewed.
4. A deployed app must obtain its permitted data from an approved source or ship only the minimum derived demonstration data explicitly cleared for release.
5. Every NASA-backed result must retain a human-readable source reference: investigation ID/title plus source-relative path and sheet/row or field where applicable.

## Attribution format

Use this pattern near data-driven findings and exports:

> Source: NASA Physical Sciences Informatics (PSI), [investigation identifier and title], `[source-relative path]`.

For a derived result, add the method/version and state that AERO-PSI performed the transformation.

## Provenance requirements

- Do not alter any original file under `DATA/`.
- Record source-relative path, source checksum, parser version, import timestamp, selected sheet, row count, and transformation version for every derived table.
- Preserve original field names and units in raw/ingested layers.
- Link each normalized record back to a source row, sheet, or time-series file.
- Label uncertainty, ambiguity, missingness, and inferred joins rather than filling them in.

## Release gate

Before public release, confirm for every shipped data artifact: source/publication status, whether it is original/transformed/aggregate, required attribution, redistribution permission, and that no personal, restricted, or unreviewed material is included.

This is an engineering policy, not a legal determination. When source terms are unclear, keep the artifact local and seek appropriate NASA/PSI guidance before release.

