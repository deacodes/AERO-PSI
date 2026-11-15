## SI workspace and copy cleanup — 15 November 2026

- [x] Remove the persistent investigation bars and floating archive SI panel; retain saved-study context internally and a local return control beside model linking.
- [x] Route archive, model, graph-point, gap and Studio dataset interpretation into the SI page, with frozen source context, follow-ups and explicit clearing.
- [x] Shorten introductions and helper text across all seven pages; retain units, provenance, scientific limitations and actionable errors.
- [x] Remove four live legacy records matching browser-test prompts; recovery copies and a manifest are in `exports/test-investigations-removed-2026-11-15`. Preserve authored and ambiguous records.
- [x] Verify 163 Python tests, shared SI browser routing and Studio regression with isolated storage and no paid AI calls.

# Current pass: actionable gaps and a connected investigation

- [x] Assess question-specific prerequisites using numeric values, report leads, and explicit source scope.
- [x] Explain what existing evidence supports and what blocks the requested conclusion; never infer a literature gap from archive absence.
- [x] Show a source-linked coverage matrix and prioritized next actions with a transparent rule and honest ties.
- [x] Carry the question, selected finding, evidence and assumptions into a saved Studio draft without requiring AI.
- [x] Preserve that draft while visiting models; attach backend-recomputed results and inputs to it.
- [x] Preserve research evidence when SI revises the saved plan; expose source and model context in the interface and exports.
- [x] Handle unsupported questions, stale selections, errors, reloads and conflicting revisions.
- [x] Test real archive workflows, backend contracts and desktop/mobile frontend parity; do not alter NASA sources.

Verification: 163 Python tests passed, including seven new readiness/handoff tests. The existing research browser regression and the new Archive → assessment → Studio → scattering → reload journey passed. Desktop/mobile layouts were inspected; source hashes matched all 180 NASA files. AI-disabled checks made no paid provider calls. Test investigations were isolated under `/tmp`, outside the user library.

Backend/frontend parity: `/research/explore` returns the assessment displayed by the gap matrix; `/atlas/plan` and the SI measurement-planning tool include that assessment. `/studio/from-research` recomputes the assessment and verifies selected rows; `/studio/attach-model` recomputes model inputs, checks the saved revision, and records provenance. Studio displays linked scenarios and retains evidence during SI revision; JSON exports contain the saved context and Markdown briefs describe linked scenarios. The active study survives navigation and reload.

Limits: requirements and priorities are declared workflow rules, not a learned novelty score. Report retrieval supplies leads rather than exhaustive review. Measurements are not automatically calibrated or comparable. Model links remain assumed scenarios, not fits to NASA measurements. Broader live SI answer evaluation and public deployment remain outside these two objectives. One concurrent browser run timed out; the isolated research regression and direct saved-record reload passed.

# AERO-PSI: full project checklist

This is the execution checklist for the **interactive web platform**. The NASA `DATA/` folder is the immutable source archive. Derived datasets, catalogs, caches, and generated outputs must live outside that folder.

## Connected workspace and SI reliability — 2026-11-14

- [x] Reproduce Studio failure: a live Vertex response could not be parsed as JSON. Add explicit response schemas, bounded output, compact citation aliases mapped to full verified IDs, and actionable format/length/provider error messages. Invalid drafts never overwrite saved work.
- [x] Verify successful live Studio generation and persistence in temporary storage; verify live model SI with a cited backend-recomputed scattering result.
- [x] Add NASA Archive → Datasets as the default archive view. Preserve Run explorer and question-specific ranking in separate tabs.
- [x] List all 180 files; show the 10 original experiment CSV tables and 103 imported run worksheets as searchable, paginated tables with all columns and source-row provenance. Reference files and unimported worksheets are explicitly distinguished.
- [x] Color-code numbers, text, blanks and possible instrument sentinels with a textual legend. Preserve zero values, missing cells and -10 source values; colors never assert scientific validity.
- [x] Add table search, row inspection, displayed-row CSV export, and links to plot, check gaps or start an investigation.
- [x] Make Gap Finder open on measurement requirements; retain evidence plots/reports and inline SI as supporting tabs, with a direct link back to complete dataset tables.
- [x] Keep coagulation/scattering SI beside the computed result; recompute inputs on the server and transfer actual model evidence into Studio planning. Contextual point failures now expose the reason instead of silently looking like successful AI.
- [x] Replace repeated homepage feature stacks with one research workflow; preserve NASA imagery and the Studio footer CTA. Preserve the active investigation title across model navigation.
- [x] Verify 156 Python tests and browser interactions at desktop/mobile widths. No original NASA files changed.

Live checks: `derived/reports/studio_vertex_check.json`, `derived/reports/model_si_live.json`. UI checks: `derived/reports/cohesion_browser.json`. The table view covers original catalog CSV rows and every row/column of imported worksheets; it does not silently import additional workbook sheets or convert reports to measurements.

## Question-led research and evidence repair — 2026-11-14

- [x] Make research creation the primary action; keep the older tool runner optional. Request question-specific method titles, with no mandatory ranking/coverage/audit trio.
- [x] Add a saved Experiment design tab: hypotheses, response variables, up to four named factors, justified ranges, controls, measurement methods and analysis criteria.
- [x] Preview evenly spaced factorial conditions with levels/replicate sliders, interactive trial plots, a trial table and CSV export. These are proposed conditions, not predicted outcomes or a power calculation.
- [x] Replace the empty/header-presence gap view with actual populated NASA experiment rows and imported signal samples. Add source selection, material filtering, axis controls, source-point selection and original row/column/hash provenance.
- [x] Match flame-size questions to flame dimensions. FLEX exposes 274 experiment rows with 197 numeric visible-flame extinction diameters; no matched acceleration history is inferred.
- [x] Separate available values, relevant report passages and measurements still needed. Missing archive fields are not claims that a gap exists in all published research.
- [x] Keep SI discussion on the evidence page; reread selected rows on the backend, retain follow-up context, and transfer the question/finding to a new investigation.
- [x] Guard stale selections and invalid source paths/signals; clear prior investigation context for a new draft; preserve saved design revisions and invalidate outdated calculations.
- [x] Validate 146 Python tests and browser workflows for research, ranking/state guards, measured-window analysis, coagulation, Mie scattering, direct SI, source drilldown and responsive layouts. All 180 original source files remain unchanged.
- [x] Verify live Vertex generation in the configured environment; completed in the connected-workspace repair above. The earlier browser pass used fixtures only.

Current validation: `derived/reports/research_browser.json`, `derived/reports/discovery_browser.json`, `tmp/ui-checks/browser-results.json`, `tmp/ui-checks/science-browser.json`. Research interpretation has bounded source context; generated scientific conclusions still require source review. The gap screen uses declared measurement requirements and retrieved passages, not a comprehensive literature-gap proof.

## Investigation Studio and frontend split — 2026-11-14

- [x] Replace the single large HTML document with separate Home, NASA archive, model workbench, gap finder, science, Resources and Studio templates; shared sidebar/settings components and feature-specific JavaScript/CSS files.
- [x] Add direct `/studio`, `/archive`, `/models`, `/gaps`, `/science`, `/resources` routes with reload and browser-history support. Preserve legacy hash links and existing mathematical workflows.
- [x] Add a full-page library of saved Studio investigations and earlier tool analyses, with search, progress, archive and restore.
- [x] Add literature, measurement analysis, simulation and physical-experiment proposal types. Specialized physics tools remain optional.
- [x] Implement bounded Vertex plan generation/revision, exact source-ID validation, detailed Markdown/LaTeX methods, required inputs, expected outputs, interpretation criteria, safety/integrity review and explicit limitations. Provider failure never becomes a fabricated preset plan.
- [x] Add editable/reorderable steps, circular completion checkboxes, observations, a notebook, saved revision history and research-brief/JSON exports. Completion records user progress, not scientific approval.
- [x] Persist work in `derived/studio`, with atomic writes and revision-conflict protection. Retain source data unchanged; test storage can be isolated through environment settings.
- [x] Connect steps to the existing allowlisted Python tools and explicit workbench inputs. Store complete calculation outputs, catalog version and implementation hashes. Changed questions/methods mark related results out of date.
- [x] Add CSV input with units/source descriptions and interactive line, scatter, bar, histogram and heatmap charts, plus dataset CSV/chart SVG exports. Preserve missing values and distinguish user-supplied data from model outputs.
- [x] Preserve complete aggregate-point row membership; allow graph selections to become research steps. SI reads saved data, receives full-scope descriptive statistics plus at most 30 explicitly labeled preview rows, and retains dataset/row/revision context with its answer.
- [x] Keep SI interpretations attached to their matching dataset; handle empty/loading/provider-error states without inventing results.
- [x] Remove the homepage pink/blue header gradient and add a footer CTA to Investigation Studio, with a secondary Resources link.
- [x] Verify the Studio workflow, real coagulation execution, source drilldown, existing model/scattering/SI workflows, light/dark styling and desktop/mobile layouts. All 180 original archive hashes remain unchanged.
- [x] Verify successful live Vertex plan generation; the later structured-output repair above passed. The original transport-error result is superseded by that live check.

Validation artifacts: `derived/reports/studio_browser.json`, `derived/reports/studio_vertex_check.json`, `derived/reports/document_review_verification.json`. Python suite: 136 tests. Local persistence is implemented; Firebase accounts, cross-device synchronization and collaboration are not part of this pass.

## Active 12-priority audit — batches of three

This tracker supersedes historical completion boxes below where they conflict. A checked implementation is not automatically UI-connected or experimentally validated. Work order: 1–3, 4–6, 7–9, 10–12; then page-by-page backend/challenge audit. Step 9 onward requires dedicated interactive design work: contextual SI, meaningful animation, linked charts, accessible exploration, and reproducible comparisons—not decorative cards alone.

### Batch 1: priorities 1–3 — foundation implemented, acceptance work still open

**1. Reconcile current state**
- [x] Identify implemented coagulation expansion versus absent optical forward physics and archive-only gap logic.
- [x] Correct homepage gravity and multi-angle claims.
- [x] Define a saved investigation schema with question, evidence, assumptions/inputs, tool outputs, failures, catalog version, and code hashes.
- [ ] Reconcile every historical checklist entry with code and UI; conduct the full page audit after priority 12.

**2. Evidence foundation**
- [x] Read-only extraction for PDF, PPTX (including speaker notes), DOCX, TXT and hash-linked legacy DOC conversion, with exact PDF-page/slide/paragraph/line locators.
- [x] Extract all 49 eligible document/text files (39 distinct contents) into 3,506 excerpts; originals unchanged. Duplicate files retain their own provenance paths.
- [x] Excerpt search and retrieval APIs; invalidate excerpts when source checksums change.
- [x] Feed document excerpts into SI retrieval with explicit unreviewed status and warnings against treating extracted equations as verified.
- [x] Review selected scientific passages across every distinct document/text source; preserve 50 source-linked review notes, classifications and limitations. Visually inspect key SAME/SAME-R/BASS equations and image-only Word content.
- [x] Record source discrepancies: SAME lognormal typography, table arithmetic, illustrative detector count, BASS heat-transfer property naming, Saffire image-offset conflict, and instrument calibration/timing caveats.
- [x] Recover the legacy DOC into a separate derived PDF, verify selected equation images and invalidate excerpts if either source or conversion changes.
- [x] Audit all 170 FLEX calibration-log rows; retain negative signals, clock offsets and repeated timestamps with distinct image counters. Do not invent radiometer units.
- [x] Add three actually consulted NIST web references with URL, access date and bounded summary; no invented browsing provenance for general AI knowledge.
- [x] Connect review notes to SI retrieval and Resources → Scientific source review, with typeset equations and drilldown to original excerpts.
- [ ] Complete exhaustive visual review/digitization of remaining figures and image-only equations. The coverage ledger explicitly distinguishes extraction from reviewed passages.
- [ ] Verify additional run-condition/calibration mappings before numerical reuse; source review does not itself create a measured PSD or validate the platform model.

Document-review checks (2026-11-14): 125 Python tests pass; desktop/mobile browser checks verify source passages, equation rendering, consulted website links and rejection of unknown sources, with no JavaScript errors. Original archive hashes checked against all 180 catalog entries; no changes. Local algebra checks verify moment inversion and identify reported numeric inconsistencies under explicit assumptions. One capped Vertex cross-check (16,665 input characters; 2,048 output-token limit) encountered a transport error; no retry or full-corpus upload was performed. Review and browser checks continued locally with paid AI disabled; the temporary test server is stopped. Coverage: `derived/evidence/review/coverage.json`; local verification: `derived/reports/document_review_verification.json`; browser verification: `derived/reports/document_review_browser.json`.

**3. SI coordinator**
- [x] Bounded Vertex-proposed or user-selected plans using allowlisted scientific tools.
- [x] Execute run inspection, existing ranking, condition coverage, sectional simulation, gravity comparison, and bounded uncertainty tools.
- [x] Save complete inputs/results and failures, retrieve investigations by ID, and synthesize with runtime evidence.
- [x] Separate general scientific reasoning from archive claims. All science questions use the AI provider; the earlier hardcoded Brownian answer was removed at the user’s request.
- [x] Provider timeout, per-request tool limits, model-size limits, explicit provider fallback, and between-tool cancellation callback.
- [ ] HTTP job cancellation, wall-clock compute budgets/concurrency limits, and follow-up investigation state.
- [ ] Live Vertex planning/synthesis evaluation and independent claim-support evaluation. Citation-ID checks are not semantic validation.
- [ ] Frontend coordinator controls, exact citation drilldowns, and page integration (priorities 9–10).

Batch-1 verification: 48 automated tests pass, including education endpoint routing, source-change invalidation, disallowed tools, missing scenarios, saved execution, tool failures, and between-step cancellation. A direct gravity-comparison example completed with AI disabled. All 180 source-file checksums match the existing catalog. No website server was started; live Vertex and browser integration are not verified in this pass.

### Batch 2: priorities 4–6 — backend delivered; evidence-dependent acceptance remains

**4. Observed-data analysis**
- [x] Explicit confirmed baseline/event/recovery windows; mean/median baseline selection.
- [x] Signed metrics with units, optional source-referenced thresholds, interpolated threshold crossings, missing/duplicate/reversed-time handling and optional time-gap cutoff.
- [x] Full selected-event CSV export with source hash, worksheet, rows, raw/corrected values and analysis metadata.
- [x] Descriptive within-run window comparison; block cross-run numerical comparisons without reviewed calibration/condition equivalence.
- [x] Exercise one PSI101 and one PSI102 import and record diagnostics in derived/reports/batch2_verification.json. These are software checks of proposed windows, not approved experimental selections.
- [ ] Independently verify selected workbook signals/window boundaries, establish run-condition joins and calibration equivalence before allowing cross-run conclusions.

**5. Coagulation verification**
- [x] Stabilize Fuchs interpolation-distance evaluation; verify against independent 60-digit arithmetic and fixed kernel reference values.
- [x] Test continuum, free-molecular and shear limits, constant-kernel analytic population evolution and known prescribed-growth grid refinement.
- [x] Add domain sensitivity with resolved number-CDF distance and initial/final moments, plus visible initial lognormal tail truncation.
- [x] Preserve conservation, overflow and underflow checks; reject unresolved distributions for optical coupling.
- [ ] Verify run-matched NASA size-distribution/time-evolution targets and experimental validation; numerical tests do not supply these missing measurements.

**6. Optical forward physics**
- [x] Pinned miepython 3.3.1 spherical Mie model; explicit vacuum wavelength, refractive index, medium index, angle and number-distribution inputs.
- [x] Gated Rayleigh approximation, cross sections, efficiencies, absorption/extinction/scattering coefficients, and normalized unpolarized angular response.
- [x] Couple optical predictions to time-resolved coagulation distributions; retain source/assumption provenance and model warnings.
- [x] Tests for published absorbing-sphere values, full-solid-angle normalization, Rayleigh limit, index matching, concentration scaling and static-population coupling.
- [x] API and SI tool integration; example requests supplied. Frontend integration remains in priority 10.
- [ ] Experimental detector-response validation, actual angle geometry, and material-specific verified optical constants remain evidence-dependent. No voltage conversion or particle-size inversion is claimed.

Verification: 72 automated tests pass after integration and boundary checks; report includes actual software-check outcomes and unchanged hashes for all 180 archive files. No server was started for this batch.

### Priorities 7–8 — implemented; scientific review remains explicit

**7. Question-specific investigation ranking**
- [x] Question/goal controls, declared lexical concepts and aliases, reproducible component scores and shared ranks for ties.
- [x] Separate question relevance, indexed measurement suitability, import QA and unestablished comparability; no scientific-importance claim.
- [x] Source weights distinguish metadata (1), observed table values (0.75), and unreviewed report mentions (0.35). Repeated files/rows do not boost relevance.
- [x] Source drilldowns, per-investigation coverage handoff, JSON export and contextual SI ranking interpretation.
- [x] Missing/zero/header-only measurement safeguards; stale and pending ranking actions disabled, including per-investigation handoffs.
- [ ] Expert relevance assessment and independently validated semantic ranking. Current scores are transparent workflow heuristics, not an AI-trained scientific relevance model.

**8. Evidence-linked gaps and measurement planning**
- [x] Question-specific prerequisite coverage with exact indexed field/source references and explicit not-located states.
- [x] Distinguish indexed measurement prerequisites, calibration/model prerequisites, same-table unrecorded conditions, unknown comparability and unestablished scientific knowledge gaps.
- [x] Replace global Cartesian gaps with bounded same-table/material/geometry/column candidates; exclude incomplete records before collecting factor levels.
- [x] Condition candidates retain one-factor reference rows, column units and source hashes; physical feasibility remains unknown.
- [x] Selectable proposal objectives, varied parameters, controls, measurements, analysis plans and expected qualitative benefit; original-report review is the first action.
- [x] Transparent priority components and honest ties; no fabricated information gain, feasibility score or predicted experiment outcome.
- [x] Interactive measurement cells, source drilldowns, condition contrast selection, plan export and allowlisted SI measurement-planning tool.
- [x] Preserve platform context separately from measured gravity; changing investigation clears obsolete run fields.
- [ ] Establish reviewed calibration/size targets and run comparability; review report passages, feasibility, operating ranges, replication and costs with scientific expertise before executing experiments.

Verification: 102 Python tests pass. Browser checks cover question-dependent reordering, source retrieval, proposal and condition selection, SI plan/execution, desktop/mobile layouts, stale/pending handoffs, exact displayed score sums and invalid-request handling. Existing coagulation/scattering/SI browser regression passes without JavaScript errors. These checks use AI-disabled deterministic execution; no new live Vertex or scientific-answer evaluation is claimed. All 180 original archive hashes match. The test server is stopped after verification.

### Requested pass: priorities 9–11

**9. Contextual SI and investigation outputs**
- [x] Build/review/execute SI tool plans using selected run, computed scenario and explicit optical inputs.
- [x] Inspect tool outcomes and provenance, reopen saved investigations, export reproducible JSON and a readable scientific Markdown brief.
- [x] Contextual scenario, scattering and distribution-time-slice SI entry points.
- [x] Separate educational/evidence modes, inspect exact source records, render sanitized Markdown and actual LaTeX using local libraries.
- [x] Clear execution, error, fallback, and changed-context states; loading a saved record invalidates stale executable plans.
- [ ] Multi-turn investigation reasoning and independently evaluated scientific claim support remain open. A citation-ID check does not establish factual entailment.

**10. Frontend integration**
- [x] Existing four main views retained, homepage remains entrance, Resources separate; shared selected-run/computed-scenario context.
- [x] Gravity/regime, gas, density, shear and removal controls connected to actual solver; preserve marked scenario comparison and grid checks.
- [x] Interactive resolved size-distribution timeline with playback, scrubbing and accessible bin readouts.
- [x] Actual Mie/Rayleigh angular response, explicit optical properties, synthetic or computed particle populations, angle readouts and SI interpretation.
- [x] Confirmed observed-data windows, baseline method, metrics and full-row/provenance exports; block incompatible marked-run overlays.
- [x] Source drilldowns, all-file resource inventory, proper scientific warnings, safe local Markdown/math rendering, keyboard graph interaction and reduced-motion behavior.
- [x] Correct stale scientific copy, show tied run readiness scores, break chart lines at missing samples, fix source-list layout and responsive views.
- [ ] Additional advanced study forms (uncertainty/calibration/domain studies), verified measured-distribution import UX, and persistent cross-session workspaces remain beyond the controls connected in this pass.

**11. Verification**
- [x] 88 Python tests pass, including 15 scripted offline SI questions and fail-closed answer contracts. These are not 15 live model evaluations.
- [x] Real-browser regression: coagulation/timeline, measured windows, computed-distribution scattering, keyboard angle readout, SI plan/execution, brief export, explanations, source drilldown, injected-script sanitization and service failure.
- [x] Six pages checked for horizontal overflow at desktop and phone widths; light mode exercised. No JavaScript exceptions in the regression.
- [x] Independent interface review: two material defects fixed and separately regression-tested; no design-system rewrite required.
- [x] Live Vertex educational answer and tool planning succeeded. Narrative synthesis failed once with a provider error and succeeded on retry; fallback remains visible.
- [ ] Broad live scientific-answer evaluation, independent claim-support review, complete screen-reader/contrast audit and NASA experimental validation remain open. Numerical/software checks do not certify scientific predictions.

### Follow-up fixes — scattering runtime and scientific answers
- [x] Ordinary CLI launch selects the existing project environment before loading scientific dependencies; verify real Mie angular scattering from `python3 -m aero_psi serve`.
- [x] Rayleigh uses its analytical implementation without requiring Mie; missing Mie is a server capability error, never an instruction to download a requirements file.
- [x] Direct scientific conversation appears before optional tool plans. General science and conditional reasoning do not require an archive match; source-specific claims still require citations.
- [x] Remove every canned scientific-answer path, including the exact Brownian-motion special case. Empty question inputs; no prefilled question silently supplied.
- [x] Retain bounded conversation context for follow-ups; clear conversation state explicitly. Render Markdown and equations safely.
- [x] General explanation plans retrieve scientific context instead of automatically ranking or auditing. Explicit ranking and measurement-planning requests retain their tools.
- [x] Distinguish actual AI generation from unavailable service; expose credential, permission, model, timeout and resource-exhaustion errors without secrets.
- [x] 117 Python tests, ordinary-launch/Mie browser check, direct-question/follow-up/no-preset regressions and existing model/SI workflows.
- [ ] Provider reliability remains external: live testing included successful scientific generation, a timeout and a 429 resource-exhausted response. Do not claim uninterrupted availability.

**Scientific document review — extraction and selected review implemented; exhaustive visual review remains open**
- [ ] Review all supplied reports and presentations scientifically, including figures, tables, equations, units, applicability assumptions, instrument geometry and calibration evidence.
- [x] Track exact page/slide/paragraph/line locators and separate reported statements from independently verified model inputs. Raw extraction remains distinguished from reviewed notes.
- [x] Resolve the legacy `PSI102/ICES Paper 2005-01-2930 rev.doc` through a separate hash-linked conversion; inspect selected image-only equations, retaining the original unchanged.
- [x] Feed the reviewed scientific notes and actually consulted web references into scientific-answer retrieval with applicability and source-discrepancy warnings.
- [ ] Reconcile reviewed findings with current coagulation/scattering physics, run mappings and scientific-answer retrieval; add supported changes only after checking equations and units.
- [ ] Separately review and integrate the externally supplied `/Users/deabhargava/Downloads/SAME_Baseline Concept Description Document_001 Rev A.pdf`; its content hash is not among the 39 distinct archive sources, so it is not included in the archive coverage totals.

Current archive status: all 49 eligible files (39 distinct contents) extracted into 3,506 searchable excerpts, supplemented by 50 source-linked review notes and three consulted NIST references. Raw excerpts retain their extraction status; notes identify the selected reviewed passages. This is not a claim that every equation or figure has been scientifically verified. Detailed completed work and remaining limits are tracked under Evidence foundation above.

### Priority 12 — not started in this pass
- [ ] Deployment, release reproducibility, final attribution and challenge-focused demonstration.

### Final acceptance audit
- [ ] Inspect homepage, Investigations, Coagulation + Scattering, Coverage + Planning, Evidence SI, Resources and settings individually.
- [ ] Cross-check every control and claim against an implemented backend capability.
- [ ] Cross-check delivered summarization, ranking, interpretation and fire-safety insight workflow against the official challenge.
- [ ] Remove redundant or unsupported features and record remaining evidence-dependent limitations.

## 0. Project guardrails

- [x] Move the NASA archive into this project at `DATA/`.
- [x] Keep source files intact: do not edit, rename, move, or write output into `DATA/`.
- [x] Inventory the archive: 180 non-system files across PSI-101, PSI-102, SAFFIRE, BASS/BASS-II, FLEX, ACME, and SOFIE.
- [x] Establish evidence labels: **Observed in source**, **Model result**, **Assumption**, **Unknown / needs data**.
- [x] Add a repository README explaining the project in one paragraph, setup steps, local run commands, and the evidence-label policy.
- [x] Add `.gitignore` for generated catalog/data/cache folders, temporary conversions, virtual environments, `.env`, and local run outputs.
- [x] Decide and document the license/attribution approach before publishing any NASA-derived data files.
- [x] Add a `DATA_DICTIONARY.md` with every derived dataset, source path, fields, units, transformation, and version.

## 1. Define the product

- [x] Lock the product name, one-sentence value proposition, and NASA Space Apps challenge framing.
- [x] Write the central demo story: **select a smoke run → inspect observed signals → explore a transparent scenario → find a missing experimental condition → receive a cited explanation**.
- [x] Define the primary audience: Space Apps judges first, then fire-safety/combustion researchers and mission designers.
- [x] Lock the MVP navigation:
  - [x] Home / mission overview.
  - [x] Run Explorer.
  - [x] Smoke Lab (coagulation scenario).
  - [x] Optical Response.
  - [x] Experiment Atlas / gaps.
  - [x] Evidence Copilot.
  - [x] Method and limitations.
- [x] Write plain-language empty states for unavailable data, bad joins, unsupported calculations, and loading errors.
- [x] Decide the only three headline user questions the MVP must answer.
- [x] Reject every feature that does not help answer one of those questions in the demo.

## 2. Backend foundation

- [x] Create a project-local, read-only NASA file catalog: `aero_psi/backend.py`.
- [x] Produce `aero_psi_catalog.json` from `DATA/`.
- [x] Verify the catalog finds 180 source files and eight investigation metadata records.
- [x] Run the local API health endpoint successfully.
- [x] Add versioned API routes and a compact API contract document.
- [x] Add an API response envelope with `data`, `source`, `warnings`, and `generated_at`.
- [x] Add structured, non-sensitive server logs.
- [x] Add a consistent error format and appropriate HTTP statuses.
- [x] Restrict the development server to `127.0.0.1` by default.
- [x] Add CORS configuration only for the site origin used by the frontend.
- [x] Add lightweight automated tests for catalog paths, file counts, metadata extraction, and CSV parsing.
- [x] Add a one-command dev launcher for backend plus frontend.

## 3. Data catalog and provenance

- [x] Parse all eight `i_Investigation.txt` records into the catalog.
- [x] Parse the 10 CSV experimental tables into the catalog.
- [x] Classify source files by format, investigation group, measurement family, candidate material, and candidate run ID.
- [x] Add an investigation record model: ID, title, acronym, platform, years, study objective, measurement family, source path, and relevance rubric.
- [x] Add the published relevance ranking: SAME-R, SAME, SAFFIRE, BASS-II, BASS, FLEX, ACME Flame Design, ACME CFI-G, SOFIE.
- [x] Store the reason for each ranking in a human-readable field.
- [x] Preserve raw experimental-table values and headers exactly in a `raw` namespace/table.
- [x] Create a normalized experimental-condition table with a source-row pointer for every derived record.
- [x] Add a field-level source path and original row number to every normalized record.
- [x] Add a transformation version and timestamp to every derived record.
- [x] Add `unknown`, `not_applicable`, `missing`, and `ambiguous` states; never replace missing values with zero.

## 4. PSI-101 / SAME-R raw-run ingestion

### Import design

- [x] Decide the derived storage format: gzip-compressed JSON Lines for the portable MVP, preserving one source row per record.
- [x] Create a `derived/` directory outside `DATA/` for generated tables.
- [x] Implement a legacy `.xls` reader/conversion workflow that writes only temporary/derived files outside `DATA/`.
- [x] Record the original file's relative path, SHA-256, selected worksheet, parser version, row count, and import warnings.
- [x] Prefer the raw/housekeeping worksheet over graph sheets for baseline ingestion.
- [x] Detect the PSI-101 raw sheet named `Original (cut and paste)`.
- [x] Detect legitimate variants rather than assuming every workbook has the same sheet name.
- [x] Exclude chart-only sheets (`1 × 1`) from data imports.
- [x] Preserve all source columns, not only the displayed signals.

### Normalize and validate

- [x] Define a canonical time-series schema with source names plus normalized aliases.
- [x] Parse `TimeString` and `Time`; store original values and a canonical UTC timestamp where valid.
- [x] Preserve `TestNumber`, `SampleNumber`, `CarouselNumber`, `RunMode`, and elapsed-test time as run metadata.
- [x] Map core signals without altering their values/units; absent fields remain explicit:
  - [x] Obscuration voltage.
  - [x] Scatter voltage.
  - [x] STS detector signal.
  - [x] Ion detector A/B signals.
  - [x] PTrak particle concentration.
  - [x] DustTrak A/B mass concentration.
  - [x] Plume temperature.
  - [x] Flow and pressure signals.
  - [x] Detector/power/state flags through preserved raw columns and run metadata.
- [x] Record source units exactly; add a normalized unit only after a documented conversion.
- [x] Detect duplicate timestamps and report, rather than silently discard, them.
- [x] Flag sentinel values such as `-10` and document the per-signal rule used.
- [x] Flag impossible time order, missing time, fully-zero measurement regions, and absent signal columns.
- [x] Keep raw signal polarity; record any display-only sign inversion separately.
- [x] Do not use graph-sheet PTrak scaling (`/100`, `/1000`, `/10000`) as a raw conversion rule.
- [x] Build a per-file import report with row count, time span, available signals, missingness, and warnings.

### Join to SAME-R conditions

- [x] Parse `PSI-101_Experimental table_SAME-R.csv` into a clean run-condition table.
- [x] Normalize material names conservatively from source paths: Kapton, Silicone, Lampwick, Pyrell, Teflon, and Dibutyl Phthalate remain distinct labels.
- [ ] Create a candidate join using material and test/run number only when evidence matches.
- [ ] Label each join `verified`, `candidate`, `ambiguous`, or `unmatched`.
- [x] Add a manual mapping file for verified raw-workbook-to-experimental-row links.
- [x] Preserve both file IDs when duplicate/variant runs exist (`63/63a`, `64/64a`, etc.).
- [ ] Never include an unverified candidate join in quantitative cross-run conclusions by default.

### MVP test set

- [ ] Ingest and inspect at least one high-quality run from each PSI-101 material.
- [ ] Select one “hero” run with clean timestamps and multiple responsive signals for the demo.
- [ ] Select one flawed/ambiguous run to demonstrate visible QA warnings.
- [ ] Document the exact run paths used in the demo and why they were selected.

## 5. PSI-102 / SAME ingestion

- [x] Reuse the import pipeline; do not create a separate incompatible parser.
- [x] Parse the PSI-102 experimental table with sample number, material, airflow, weight-loss rate, and aging duration.
- [x] Account for its incomplete mapping to the raw workbooks.
- [ ] Handle multiple-test, multiple-peak, average, and log files as distinct data roles.
- [ ] Deduplicate only with a recorded rule using source path, timestamp range, and test number.
- [x] Mark logs as event/context records, not measurement time series.
- [ ] Select one clean PSI-102 comparison run.
- [ ] Keep PSI-101 and PSI-102 separate by default; show their different dates, materials, conditions, and processing conventions.
- [ ] Forbid direct pooled statistical claims until calibration and controlled-condition equivalence are established.

## 6. Metrics and observed-data analysis

- [ ] Implement a user-confirmed test window: pre-event baseline, heating/test period, recovery period.
- [x] Offer a proposed window from documented state signals, but never silently assert it is ground truth.
- [x] Store window boundaries and method with every metric result.
- [ ] Implement baseline statistic selection (median default; mean optional).
- [x] Implement baseline-corrected signal without overwriting raw values.
- [x] Implement peak, minimum, time-to-peak, area under curve, duration above threshold, and missingness fraction.
- [ ] Define each metric's units, sign convention, and unavailable-data behavior.
- [x] Use no threshold until its origin is stated; use relative/user-adjustable thresholds if no calibration exists.
- [x] Add sensor alignment/lag view rather than asserting causality.
- [ ] Add run-to-run comparison only for selected metrics, material/condition grouping, and verified joins.
- [ ] Add download of selected observed series and metrics with source provenance.
- [x] Add deterministic tests using tiny known time-series fixtures.

## 7. Deterministic coagulation scenario engine

### Backend expansion audit — 14 November 2026

- [x] Selectable continuum, slip-corrected and Fuchs Brownian kernels; gravity-dependent differential settling and prescribed laminar shear.
- [x] Gas pressure/molar mass/mean-free-path inputs and per-bin Knudsen/slip/settling diagnostics.
- [x] Prescribed wall loss, dilution and well-mixed settling deposition with volume accounting.
- [x] Full bin-number distributions, dN/dlnD, surface area and volume/mass moments at output times.
- [x] Explicit grid bounds and source-referenced initial bin distributions with number/volume-preserving remapping inside the grid.
- [x] Prescribed particle-number injection at specified diameters (can represent assumed nucleation or smoke injection rates).
- [x] Prescribed constant diameter growth/shrinkage with signed vapor-exchange and underflow budgets. This is not a DBP thermodynamic model.
- [x] Parameter sweeps including gravity comparison: POST `/api/v1/models/coagulation/sweep` with `scenario`, `parameter`, and `values` (maximum 12).
- [x] Observation comparison: POST `/api/v1/models/coagulation/compare-observations` with `scenario`, `observable`, and `observations` containing `time_s`, `value`, `source.reference`; returns residuals, RMSE, MAE and bias. User-supplied references are not independently verified.
- [ ] Report-derived DBP vapor properties, coupled vapor depletion, condensation/evaporation thermodynamics and nucleation kinetics.
- [ ] Pyrolysis-to-aerosol source conversion with yield and chamber-volume evidence.
- [ ] Turbulent collision kernels with applicability checks; charge and nonspherical morphology.
- [x] Seeded Monte Carlo propagation of explicit independent uniform/log-uniform input assumptions; retain sampled parameters and time-resolved 5/50/95 percentiles. POST `/api/v1/models/coagulation/uncertainty`.
- [x] Bounded single-parameter grid calibration with objective profile, boundary/flat-objective indicators, and optional held-out times. POST `/api/v1/models/coagulation/calibrate`. Analytic synthetic dilution benchmark passes.
- [ ] Correlated uncertainties, measurement-error weighting, multi-parameter identifiability and independently verified experimental holdouts.
- [ ] Extract and verify NASA size-distribution targets; execute numerical NASA validation and report actual residuals.
- [x] Combined bin-count/time-step refinement with final-moment differences and material-budget diagnostics. POST `/api/v1/models/coagulation/convergence`.
- [ ] Extend convergence checks across grid bounds and growth-remapping diffusion; independent Fuchs benchmark values.


- [x] State in the API that this is a model scenario, not a NASA measurement.
- [x] Select a simple, reproducible formulation: documented analytic monodisperse constant-kernel moment scenario.
- [x] Implement the continuum, equal-size Brownian coagulation kernel first.
- [x] Use an analytic constant-kernel solution rather than a numerical timestep/bin scheme for v1; a future sectional solver must add bin/timestep sensitivity tests.
- [x] Expose all non-source inputs:
  - [x] Initial number concentration.
  - [x] Initial median diameter.
  - [x] Distribution width.
  - [x] Particle density.
  - [x] Gas temperature.
  - [x] Gas viscosity.
  - [x] Residence/aging time.
  - [x] Sticking efficiency.
- [x] Where a value comes from a source run, show the source field, unit, explicit conversion, and rejected-value state before user use.
- [x] Where a value is not in the source, label it an assumption and show a plausible/default rationale.
- [x] Enforce nonnegative particle concentrations.
- [x] Add mass/volume conservation checks appropriate to the formulation.
- [x] Add timestep/bin sensitivity checks. (Not applicable to the analytic v1 solution; this is explicit in the API.)
- [x] Return a validation warning that no measured size-distribution target is used.
- [x] Show model curves separately from observed sensor curves.
- [ ] Support compare/reset/shareable scenario states.
- [x] Write unit tests for conservation, zero concentration, and invalid input handling.

## 7A. Coagulation validity and evidence bridge

- [x] Add a continuum-regime applicability assessment when mean free path is supplied; report `not_assessed` otherwise.
- [x] Link the model response to relevant supplied NASA report context without treating it as a calibration target.
- [x] Implement a separate continuum-regime discrete sectional solver with adaptive stability rule, volume-conservation check, and top-bin-overflow diagnostic.
- [x] Add a transparent section-count sensitivity endpoint for the sectional solver.
- [ ] Extract and verify all relevant report/PDF/PPT equations, variable definitions, ranges, and calibration scope before extending the current continuum sectional solver into transition/slip physics.
- [ ] Add a separate, source-supported transition/slip or sectional solver only after its required inputs and validation targets are available.
- [ ] Link a scenario to a measured size-distribution target only with an explicit source/run/condition match.

## 8. Optical-response module

- [x] Start with measured detector data: scatter voltage, obscuration voltage, ion signals, PTrak, DustTrak.
- [x] Return raw, baseline-corrected source-derived metrics distinctly where a validated event window exists.
- [x] Preserve sensor units and label scatter as detector voltage unless a calibration source is supplied.
- [x] Return signal availability and source quality/missingness warnings from the importer.
- [x] Compute source-derived baseline, peak, AUC, event-to-peak timing, and relative-threshold duration; provide a non-causal lag/correlation screen with warnings.
- [x] Do not claim absolute extinction coefficient, particle diameter, or detector alarm performance from raw voltage alone.
- [ ] If adding physics, require explicit wavelength, complex refractive index, geometry, and size distribution inputs.
- [ ] Gate Rayleigh approximation to a documented size-parameter range.
- [x] Use Mie theory only if inputs and implementation are verified; otherwise omit it from the MVP. (Omitted; no unverified optical-physics curve is exposed.)
- [ ] Label all theoretical curves as relative/scaled unless a calibration chain is present.

## 9. Experiment Atlas and gap finding

- [x] Normalize investigation-level fields: investigation, platform/gravity, material/fuel, geometry/flame type, O2, pressure, flow, duration, aging, outcome, measurement family, data level. (Unknown/missing states remain explicit rather than inferred.)
- [x] Build an initial coverage matrix with investigation, material, and measurement-family fields.
- [x] Include direct-measurement versus structured/document-context data-level state.
- [x] Use visible, explainable coverage rules (source-file presence only in v1).
- [x] Define the initial gap as “no cataloged supplied file for this selected factor combination.”
- [x] Separate a catalog gap from a real-world scientific knowledge gap.
- [x] Link every initial matrix cell to its supporting source files.
- [x] Add a “suggested next measurement” template based on the selected catalog gap, marked as a proposal.
- [x] Do not use an opaque ML score as the gap ranking.

## 10. Evidence Copilot

- [x] Decide whether AI is available in the deployed environment; provide a graceful non-AI fallback. (Local Vertex AI via ADC is optional; source-only fallback is built.)
- [ ] Build a retrieval index over metadata, CSV rows, derived QA reports, selected document excerpts, and run metrics.
  - [x] Index catalog metadata, normalized CSV records, imported-run QA records, and source-derived run metrics.
  - [x] Index PDF/PPTX/DOCX/DOC/TXT excerpts with source-range QA; retain unreviewed status on raw extraction and separate source-linked review notes.
- [x] Keep source chunks/records with exact path, sheet/range/row identifier, and title.
- [x] Use a strict answer contract:
  - [x] Observed in source.
  - [x] Model result (assumptions stated).
  - [x] Unknown / limitation.
  - [x] Sources.
- [x] Require a source reference for each factual/numerical claim.
- [x] Validate cited paths/rows before displaying a response.
- [x] Disallow fabricated citations, uncited conclusions, and claims of causality from co-varying signals.
- [x] Make the assistant refuse/redirect when requested values are absent from the archive.
- [ ] Add at least 15 scripted evaluation questions: direct lookup, comparison, missing data, model assumptions, and adversarial hallucination prompts.
- [ ] Manually inspect each test answer before demo day.

## 11. Website and interaction design

- [ ] Choose the framework/build approach and initialize the frontend project.
- [ ] Add a responsive app shell, navigation, mobile menu, and keyboard-accessible focus behavior.
- [ ] Create the Home page: purpose, NASA evidence base, simple architecture graphic, and “Explore a run” call to action.
- [ ] Create the Run Explorer:
  - [ ] Investigation/material/run selector.
  - [ ] Source-path and join-confidence display.
  - [ ] Run metadata card.
  - [ ] Interactive time-series chart with signal toggles.
  - [ ] Event-window controls.
  - [ ] QA warnings and data availability.
  - [ ] Computed metrics panel.
- [ ] Create the Smoke Lab:
  - [ ] Assumptions panel.
  - [ ] Model-result chart.
  - [ ] Conservation/status checks.
  - [ ] Compare/reset scenario controls.
  - [ ] Explicit “model, not measured data” label.
- [ ] Create Optical Response:
  - [ ] Scatter/obscuration/particle/detector alignment chart.
  - [ ] Metric cards with units.
  - [ ] Calibration and limitation notice.
- [ ] Create Experiment Atlas:
  - [ ] Investigation cards/ranking rubric.
  - [ ] Filterable coverage matrix.
  - [ ] Source drilldown.
  - [ ] Gap card and proposed next measurement.
- [ ] Create Evidence Copilot:
  - [ ] Question input and curated example prompts.
  - [ ] Structured response sections.
  - [ ] Clickable source citations.
  - [ ] Clear empty/error/refusal state.
- [ ] Create Methods and Limitations page.
- [ ] Use readable typography, high contrast, responsive charts, accessible colour choices, and no colour-only meaning.
- [ ] Add loading skeletons and specific error messages.
- [ ] Add downloadable selected data/scenario output only if it can retain provenance.

## 12. Integration and API contracts

- [ ] Connect frontend selectors only to imported/verified backend records.
- [ ] Add APIs for investigation catalog, source files, normalized run list, run metadata, time series, metrics, model scenarios, atlas coverage, and citations.
- [ ] Validate all request parameters, numeric ranges, and file identifiers.
- [x] Paginate or downsample large time series without changing source values.
- [ ] Preserve raw-resolution download separately from chart downsampling.
- [ ] Cache catalog/derived reads safely; invalidate after a documented re-import.
- [ ] Test all API error states in the interface.
- [x] Ensure no API returns filesystem paths outside the intended project source reference.

## 13. Scientific, data and software QA

- [ ] Recount catalog files against `DATA/` before release.
- [ ] Verify every demo source path exists.
- [ ] Verify every displayed number has either a source record or a stated formula/assumption.
- [ ] Spot-check at least 10 imported runs against the original workbook headers, row counts, start/end timestamps, and selected signals.
- [ ] Verify sign/scaling for every displayed detector and PTrak/DustTrak series.
- [ ] Verify event-window metrics with an independent hand calculation for at least two runs.
- [ ] Test all missing/zero/sentinel/duplicate timestamp paths.
- [ ] Test model conservation and invalid-input safeguards.
- [ ] Verify all citations open the corresponding internal source record/view.
- [ ] Run the AI evaluation questions and log failures.
- [ ] Test desktop, laptop, tablet, and phone layouts.
- [ ] Test keyboard navigation, focus visibility, text contrast, chart legend toggles, and screen-reader labels.
- [ ] Test app behavior with backend unavailable and with an empty/invalid selection.
- [ ] Do a final source-archive integrity check: no files inside `DATA/` changed.

## 14. Demo, documentation and submission

- [ ] Create an architecture diagram: NASA source archive → import/QA → derived evidence store → API → interactive platform → cited AI.
- [ ] Create a short demo script (90 seconds) and a longer judge walkthrough (3 minutes).
- [ ] Record the demo with a dependable fallback screen capture.
- [ ] Prepare a one-slide “what is observed versus modeled” explanation.
- [ ] Prepare a one-slide source and limitations statement.
- [ ] Write a concise README with local setup/run commands and sample URLs.
- [ ] Add screenshots/GIFs to the README.
- [ ] Add a reproducibility guide: reindex data, import a selected run, run tests, start application.
- [ ] Build and test the production artifact.
- [ ] Deploy the website or prepare a reliable local/offline demo package.
- [ ] Verify deployed environment variables, data availability, citations, and API responses.
- [ ] Practice the handoff: problem, NASA evidence, interaction, limitation, impact.

## 15. 36-hour MVP cut line

**Must ship:**

- [ ] PSI-101 catalog plus at least five imported/QA-checked runs.
- [ ] One excellent Run Explorer journey with real time-series data.
- [ ] Baseline/peak/AUC metrics with saved window configuration.
- [ ] Brownian coagulation scenario with visible assumptions and conservation check.
- [ ] Optical-response charts with correct raw units and limitations.
- [ ] Investigation Atlas with transparent ranking and coverage/gap logic.
- [ ] Evidence Copilot or, if unavailable, a citation-first evidence panel.
- [ ] Responsive website, methods page, README, and 90-second demo.

**Ship only if time remains:**

- [ ] PSI-102 raw-run import and comparison.
- [ ] Advanced multi-run comparisons.
- [ ] Document retrieval over PDF/doc/presentation text.
- [ ] Mie-theory or calibrated optical calculations.
- [ ] User accounts, saved cloud workspaces, collaboration, or database persistence.

**Do not attempt in the MVP:**

- [ ] Train a predictive ML model from heterogeneous workbooks.
- [ ] Claim particle sizing, detector certification, or causal material ranking from raw signals alone.
- [ ] Fully automate TEM/image processing without the underlying image corpus and validation.
- [ ] Pool all NASA investigations as one statistically comparable dataset.


## Homepage and SI evidence selection — 2026-11-15

- [x] Restore researcher-facing explanations and stacked homepage sections with expandable cards and selectable research examples.
- [x] Browse and preview NASA datasets inside SI; attach a table while preserving the draft question. Table context explicitly covers columns and up to three sample rows.
- [x] Offer project evidence, general scientific knowledge, or both; apply the selected scope in contextual backend requests and distinguish generated answer origins. No web-search claim.
- [x] Verify 166 backend tests and browser tests for homepage interactions, evidence selection, source-mode isolation, and existing contextual SI actions. Browser AI calls mocked; no paid calls.

### Homepage narrative and scientific help
- [x] Remove sidebar archive connection status and dot.
- [x] Group dataset actions into investigation and SI actions.
- [x] Reorder homepage: introduction, importance with NASA imagery, problem, platform approach, interactive examples and boxed CTA; expand paragraph explanations.
- [x] Add keyboard/touch/hover help for source headers and technical model inputs; retain original headings and flag unverified definitions.
- [x] Verify archive help interactions, action grouping, homepage ordering and existing evidence attachment in browser tests.

## SI-led gap review — 15 November 2026
- [x] Default Gap Finder to explicit SI review; retain a separately selected basic evidence check. Navigation alone does not trigger paid calls.
- [x] Two-stage structured Vertex review: semantic question interpretation and bounded source/column tool requests, followed by source-linked synthesis.
- [x] Validate selected investigations, exact table paths/fields and citation identities; no generated-code execution or invented measurements.
- [x] Show clarification, out-of-scope and provider failure separately without substituting canned findings.
- [x] Show requirements, supported evidence, unresolved questions, next actions, source excerpts and tool trace; export review and draft a Studio investigation.
- [x] 175 backend tests passed; SI-state browser test passed. One live two-call Vertex review successfully interpreted everyday wording about thinner air, selected three investigations and used actual column summaries.
- [ ] Independent evaluation of scientific claim support and broader question coverage remains necessary; successful generation is not scientific validation.

### Gap review clarification and measurement selection
- [x] Treat complementary measurements and run conditions as joint review scope; only an unidentified research objective blocks review.
- [x] Verify the previous broad PSI101 smoke-growth question produces a live SI assessment rather than an optional clarification.
- [x] Open the table and plot fields requested by SI; expose View selected measurements.
- [x] 182 backend tests passed; browser verification includes SI-selected plot fields and review states.
