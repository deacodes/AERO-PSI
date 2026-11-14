# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

NASA Space Apps judges, students, fire-safety researchers, and mission designers exploring spacecraft-smoke evidence.

## Product Purpose

AERO-PSI is an SI-powered, gravity-contextualized aerosol coagulation and multi-angle scattering platform with automated experiment-gap finding, source-backed run evidence, and cited scientific interpretation.

## Positioning

It keeps observations, deterministic model results, assumptions, and unknowns visibly separate while still making the archive approachable to non-specialists.

## Operating Context

Users explore investigation records, raw/housekeeping time series, deterministic coagulation scenarios, multi-angle detector response, and condition-coverage gaps through a local Python API. The sphere solver supports selectable Brownian regimes, gravity-dependent settling, prescribed shear and removal. Optical forward calculations remain distinct from recorded detector voltages; experimental NASA validation is not established.

## Capabilities and Constraints

The frontend uses HTML, CSS, and JavaScript; Python owns source ingestion, models, provenance, and Vertex AI calls. Graph points can request SI interpretation only after the backend recomputes the model point or rereads the exact source row. Original files in `DATA/` are read-only. AI must cite retrieved supplied evidence and must not infer particle size, calibration, causality, or a scientific prediction where the archive cannot support it.

## Brand Commitments

AERO-PSI is approachable, scientifically serious, spacious, and available in composed dark and light themes. Its scientific-instrument base is energized with restrained blue, pink, mint, amber, and cyan accents, softly elevated interactive surfaces, and occasional low-contrast gradients. Motion is reserved for meaningful discovery, graph, and SI explanation changes.

## Evidence on Hand

The local archive contains NASA PSI investigation metadata, CSV experimental tables, reports, and PSI-101/PSI-102 workbooks. The backend serves catalog, optical, model, atlas, and Evidence Copilot routes.

## Product Principles

1. Trace every claim to a source, formula, or explicit assumption.
2. Make scientific uncertainty legible instead of hiding it.
3. Let comparison states be saved and inspected reproducibly.
4. Use AI to summarize, rank, and interpret evidence without replacing scientific judgment.
5. Organize the interface around one traceable loop: choose evidence, inspect or model response, expose gaps, then interpret within the evidence boundary.

## Accessibility & Inclusion

Support dark, light, and high-contrast themes, text-size choices, reduced motion, keyboard navigation, visible focus, and non-color-only chart distinctions.
