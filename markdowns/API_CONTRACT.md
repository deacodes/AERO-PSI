# AERO-PSI API contract v1

The local server defaults to `http://127.0.0.1:8000`. Each v1 response wraps its result as `data`, `source`, `warnings`, and `generated_at`.

| Route | Purpose |
|---|---|
| `/api/v1/health` | Confirm server and catalog availability. |
| `/api/v1/summary` | Counts by format, group, and experiment record. |
| `/api/v1/investigations` | Ranked investigation records with relevance rationale. |
| `/api/v1/tables` | CSV schemas, row counts, summaries, previews. |
| `/api/v1/raw-tables` | Original CSV headers and rows in `raw` namespace; development-only and potentially large. |
| `/api/v1/experiments` | Normalized experimental conditions with field-level source provenance. |
| `/api/v1/files?group=PSI101&role=…` | File inventory filtered by group and/or role. |
| `POST /api/v1/models/coagulation` | Run the deterministic, assumption-explicit Brownian coagulation scenario. JSON body may set SI-valued inputs: `initial_number_concentration_m3`, `initial_median_diameter_m`, `initial_geometric_std_dev`, `particle_density_kg_m3`, `gas_temperature_k`, `gas_viscosity_pa_s`, `residence_time_s`, `sticking_efficiency`, optional `gas_mean_free_path_m`, and `output_points`. It returns a model result, conservation check, continuum-applicability assessment, assumptions, warnings, and source reference—not a NASA measurement. |
| `POST /api/v1/models/coagulation/sectional` | Run a discrete, mass-conserving continuum Brownian sectional scenario. Inputs add `section_count` and `stability_fraction`; output reports numerical steps, top-bin overflow, and conservation error. |
| `POST /api/v1/models/coagulation/sensitivity` | Run the sectional scenario at several `section_counts` and return a transparent convergence comparison. |
| `POST /api/v1/copilot` | Citation-first Evidence Copilot. Send `{"question":"..."}`. It retrieves only supplied catalog/CSV/run-QA evidence, calls configured Vertex AI through the local server, and withholds malformed or unverifiable model citations. It falls back to source records when Vertex is not configured or unavailable. |
| `/api/v1/optical/runs?group=PSI101` | Imported run list with actual available optical/detector columns and source-quality state. |
| `/api/v1/optical/summary?source_path=…` | Source-derived baseline/peak/AUC metrics for one imported run. Detector voltage is not converted to optical properties. |
| `/api/v1/optical/time-series?source_path=…&signals=scatter_voltage,obscuration_voltage&max_points=1000` | Unaltered selected source samples, downsampled by source-row selection only. |
| `/api/v1/optical/lag?source_path=…&left=scatter_voltage&right=ptrak_particles_per_cc` | Within-run association screen with explicit non-causality and sampling-regularity warnings. |
| `/api/v1/atlas/coverage` | Transparent file-backed coverage cells with source paths. |
| `/api/v1/atlas/gaps?group=PSI102` | Catalog gaps: no supplied file for a factor combination, never asserted as a real-world knowledge gap. |
| `/api/v1/atlas/conditions?group=PSI101` | Source-row-linked condition records from the supplied structured tables. |
| `/api/v1/atlas/condition-gaps?dimensions=material_or_fuel,flow,duration_or_aging` | Transparent cartesian gaps among observed structured-condition values. |
| `/api/v1/atlas/suggested-measurement?gap_index=0` | Proposal template for one condition gap, never a scientific finding. |

Unknown routes return a structured `404`. Legacy unversioned catalog routes remain aliases during local development.


## SI investigation foundation (batch 1)

- `POST /api/v1/copilot`: `{ "question": "what is Brownian motion?", "mode": "auto" }`. Modes: `auto`, `evidence`, `explain`. Educational answers are never NASA experimental findings. Offline Brownian definition is available; other general explanations require Vertex.
- `POST /api/v1/evidence/search`: `{ "question": "smoke particle size" }`. Returns up to ten extracted excerpts with hashes, locators, and review status. Extraction is not scientific verification.
- `POST /api/v1/evidence/excerpt`: `{ "id": "document:..." }`. Returns the exact indexed excerpt; changed source hashes invalidate it.
- `POST /api/v1/si/investigate`: `question`, `action` (`plan` default or `execute`), optional `source_path`, `group`, `scenario`, `uncertain_inputs`, and `plan`. A plan has 1–4 unique `{tool, reason}` steps. No shell, arbitrary file access, or generated model parameters are accepted. Vertex may select tools; when unavailable the response explicitly identifies its deterministic fallback.
- Allowed tools: `rank_investigations`, `inspect_run`, `coverage_gaps`, `simulate_coagulation`, `gravity_comparison`, `uncertainty`. Model tools require a user-supplied scenario. Gravity comparison uses 0 and 9.81 m/s². Uncertainty uses eight samples and seed zero with supplied bounds. Existing solver defaults still apply to omitted scenario fields.
- `GET /api/v1/si/investigation?id=...`: load a saved investigation. Records include evidence, complete outputs, failures, supplied inputs, catalog version, and implementation hashes.

Execution is currently synchronous. Model calls are bounded to 64 bins, 101 output points, and 600 simulated seconds; these are not wall-clock guarantees. Vertex calls have a 30-second timeout. Cancellation is supported between tool calls through the Python coordinator callback, not yet through an HTTP job interface. Saved investigations are local to the development installation; authentication is required before any multi-user deployment.

## Batch 2: observed analysis and optical physics

Use the project virtual environment (`.venv/bin/python`) with `requirements.txt` installed; Mie calculations use pinned `miepython==3.3.1`.

- `POST /api/v1/observed/analyze`: `source_path`, `signal`, `confirmed: true`, `time_unit: "s"`, `baseline_rows: [first,last]`, `event_rows: [first,last]`, optional `recovery_rows`, `baseline_method` (`median` default or `mean`), `max_interval_s`, and `threshold: {kind: "absolute" | "relative_peak", value, reference}`. Row limits are inclusive. Seconds are explicitly confirmed by the caller. No threshold is applied by default. Time reversal withholds time metrics; missing and duplicate-time intervals are skipped. Long time gaps can be excluded explicitly. Multiple TestRunning episodes are flagged. Source hashes must still match.
- `POST /api/v1/observed/export`: same request; returns full selected-event CSV plus provenance/window/metric metadata. No chart downsampling.
- `POST /api/v1/observed/compare`: `{left: analysis_request, right: analysis_request}`. Supports descriptive same-signal, same-source window comparisons. Cross-run quantitative differences remain blocked until independently reviewed condition/calibration equivalence exists; currently no override bypasses this.
- `POST /api/v1/models/coagulation/domain-study`: `{scenario, domains: [{diameter_min_m, diameter_max_m, section_count}, ...], reference_index?}`. Two to four domains; returns initial/final moments, budgets, and integrated number-CDF distance in log diameter. Changing domains can change initial discretization.
- `POST /api/v1/models/scattering`: see `examples/scattering.json`. Explicit vacuum wavelength, absolute particle index `{n,k,reference}`, optional nonabsorbing medium index (default 1), ordered angles, and source-referenced bin-number distribution. Returns Mie or gated Rayleigh efficiencies, cross sections, volume scattering/extinction/absorption coefficients, angular scattering coefficient and normalized phase function. Incident light is unpolarized. No detector voltage, multiple scattering, particle-size inversion or nonspherical optics.
- `POST /api/v1/models/coupled-optics`: `{scenario, optics}`; see `examples/coupled_optics.json`. Uses actual computed sectional distributions at each time. Maximum 64 bins and 21 output times. Rejects substantial overflow, underflow, initial tail truncation, or failed volume budgets. It does not insert optical properties from a material name.

The SI coordinator additionally accepts `analyze_observed`, `scattering`, and `coupled_optics` tools with explicit `observed_request`, `optical_request`, and `coupled_request` inputs. Results are saved with the investigation. Numerical benchmarks do not constitute NASA experimental validation.

## Source inspection

`POST /api/v1/evidence/record` accepts a known `{id}` from retrieval and returns the matching metadata, table, run-QA or document record. Unknown IDs are rejected; arbitrary filesystem paths are not accepted.
