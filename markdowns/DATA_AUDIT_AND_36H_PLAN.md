# AERO-PSI NASA data audit and 36-hour build plan

**Audit date:** 2026-11-14. **Source root (read only):** `/Users/deabhargava/Downloads/DATA`.
All 180 non-system files were enumerated; 103 legacy `.xls`, 18 `.xlsx`, 10 `.csv`, 17 `.txt`, 24 `.pdf`, 4 `.docx`, 3 `.pptx`, and 1 `.doc` files are present. The source collection was not edited. Workbook structure was read by converting the 103 legacy workbooks to temporary copies only.

## Decision in one sentence

Build the first release around **SAME-R / PSI-101**, with **SAME / PSI-102** as an earlier comparable cohort; show an explicitly deterministic aerosol-growth scenario and a detector-response/optical-proxy analysis, then use the remaining NASA studies as a transparent investigation catalog and gap map. Do not present an inferred particle-size distribution, detector calibration, or causal materials ranking as a measured result unless its source field and calculation are shown.

## Evidence, not product promises

| Claim | Status | Why |
|---|---|---|
| SAME-R was intended to relate low-gravity smoke particle size distribution to generation and transport conditions. | Supported | PSI-101 investigation metadata states that objective and documents 66 flight test points. |
| SAME/SAME-R raw workbooks contain timestamped detector, particle-count, mass-concentration, temperature, flow, pressure, state and actuator signals. | Supported | The raw-workbook headers include PTrak, DustTrak, obscuration/scatter, ion detectors, plume temperature, LFE/MFC flow, pressures, aging channels and device states. |
| The raw signals permit reproducible within-run time-series summaries and cross-run detector-response comparisons. | Supported with QA | Time, test/sample identifiers and the signals exist. Event windows, baselines, missing samples, calibration and run-to-test joins must be verified per run. |
| The supplied files alone identify physical particle diameter or refractive index for every run. | Not supported | Raw run sheets have no direct diameter/refractive-index field. The combined-results workbook contains TEM/binned/lognormal-analysis sheets, but it is not a clean universal per-run join. |
| A Brownian-coagulation simulation can be calculated. | Proposed model | It requires declared inputs/assumptions such as temperature, viscosity, particle density, initial distribution, concentration and residence time. It is a scenario, not validation. |
| Scattering can be calculated from first principles for every source. | Proposed conditional model | Rayleigh/Mie calculations need wavelength and complex refractive index, neither is consistently supplied. The MVP should expose a proxy and label assumptions. |
| AI can discover scientific facts absent from source data. | Not supported | AI can retrieve, summarize, compare and explain cited source evidence; it must not fabricate measurements, citations, causality or uncertainty. |

## Exact source inventory and usable coverage

### Direct smoke/aerosol evidence — priority 1

| Investigation and exact location | Contents and run coverage | Measurement viability / limits |
|---|---|---|
| `PSI101/PSI-101_metadata_PSI-169_SAME-R/i_Investigation.txt` | SAME-R, PSI-101, ISS, 2010; stated focus on smoke sizing/transport and detector response. | Canonical provenance and scientific framing. |
| `PSI101/PSI-101_Experimental table_SAME-R.csv` | 109 rows: Kapton 29, Silicone 22, Lampwick 20, Pyrell 20, Teflon 18. Columns: sample type, test number, description, date, inlet velocity, Rt/R0, duration, primary aging/mixing/net aging time. | Main run catalog. Dates omit year; some aging fields are blank. It does not carry a raw-workbook filename key. |
| `PSI101/{Kapton,Pyrell,Silicone,Teflon} Runs/` | 50 `.xls` raw-run files plus 8 `.xlsx` aging/analysis workbooks. Raw file coverage: 16 Kapton, 14 Pyrell, 9 Silicone, 11 Teflon. | Strongest MVP input. Raw runs commonly have a 98-column housekeeping sheet and a derived graph sheet. Material/run parsing must be filename-based and labeled as such until joined to the experiment table. |
| `PSI101/Combined SAMER Results 06 02 14.xlsx` | Large multi-sheet compiled result/analysis workbook. Sheets include material-specific response/transport views, SAME-R/SAME result sources, TEM morphology, binned distributions, lognormal-size calculations, ANOVA and size-distribution calculations. | Rich evidence, but formulas/links and heterogeneous sheets make it unsuitable as an uninspected single source of truth. Use only after extracting a documented, traceable subset. |
| `PSI101/SAMER_Final 0602 2014.pdf`, `PSI101/SAME EIRD Rev 2.00 02-25-05 HIgh Q.pdf`, `PSI101/SAME ICES  2013 07 15 final as presented.pptx` | Final report, requirements/design documentation, presentation. | Citation/context; not the MVP numerical input until fields/tables are manually extracted and checked. |
| `PSI102/Metadata/i_Investigation.txt` | Original SAME (PSI-102) metadata. It describes detector/video operation, thermal-precipitator TEM analysis, mass loss and the numerical-code objective. | Direct scientific provenance. It also records that original TEM grids were contaminated; do not imply universal TEM ground truth. |
| `PSI102/PSI-102_Experimental table_SAME (1).csv` | 8 rows with sample number/material, airflow (cm/s), weight-loss rate (mg/min), aging duration (min). | Useful conditions table, but materially incomplete relative to 53 workbooks and lacks robust file/run IDs. |
| `PSI102/{Dibutyl Phthalate,Kapton,Lampwick,Silicone,Teflon,housekeeping}/` | 53 `.xls` raw/derived workbooks and 5 `.xlsx` logs/housekeeping files: DBP 24 data + 3 logs; Kapton 6; Lampwick 5; Silicone 7 + 1 log; Teflon 8 + 1 log; housekeeping 4. | Earlier comparison cohort. Several files cover multiple tests/peaks; deduplicate by timestamp/test number, not filename. |
| `PSI102/SAME Final Science report  03 18 10 with papers attached (1).pdf`, `PSI102/SAME EIRD Rev 2.00 02-25-05 HIgh Q (1).pdf`, `PSI102/ICES Paper 2005-01-2930 rev.doc`, `PSI102/SAME ICES  2013 07 15 final as presented.pptx` | Reporting/design context. | Citation/context only for 36-hour release. |

**Raw workbooks, observed schema.** The canonical raw/housekeeping sheet is commonly 98 columns and 1,100–10,500 rows; the common PSI-101 raw sheet is named `Original (cut and paste)`, while PSI-102 varies by run. Key columns are `TimeString`, `Time`, `RunMode`, `TestNumber`, `ElapsedTestTime(Secs)`, `SampleNumber`, `CarouselNumber`, `GasPlumeTemperature(DegC)`, `SampleResistance(Ohms)`, `ISSDetectorObscurationMeasurement(Volts)`, `ISSDetectorScatterMeasurement(Volts)`, `STSDetectorMeasurement(Volts)`, `IonDetectorA/BMeasurement(Volts)`, `PTrakMeasurement(PtPerCC)`, `DustTrakA/BMeasurement(MgPerM3)`, `DustTrakA/BAnalogMeasurement(Volts)`, `LFEFlowRate[AT08](SCCM)`, MFC flow/temperature/pressure, pressures, thermal-precipitator states and detector/power/solenoid state fields.

Derived sheets commonly graph a reduced 10–25-column selection. They sometimes invert scattering sign, reset time to zero, and scale PTrak by 100, 1,000, or 10,000. **Never mix raw and graph-sheet series without inspecting the formula/scaling.** Chart-only sheets are effectively empty (`1 × 1`), not data.

### Adjacent studies — useful, but not smoke-aerosol substitutes

| Rank | Exact location | What is actually available | Appropriate use |
|---:|---|---|---|
| 3 | `SAFFIRE/PSI-98_metadata_PSI-166_SAFFIRE-I/i_Investigation.txt`; `SAFFIRE/PSI-98_Experimental table_SAFFIRE-1.csv`; `SAFFIRE/SAFFIRE-1_MergeResult-jpeg_Update_Final_v2.xlsx` | Large-scale SIBAL fire context. The CSV has 4 sample/video rows: dimensions, 20 cm/s airflow, O2, ignition and burn time. The workbook is a huge image/ZIP receipt and timestamp index, not the images themselves. | Fire-scale/context catalog; do not claim usable flame image analysis from an index alone. |
| 4 | `BASS-II/PSI-25_Experimental table_BASS-II.csv`; `BASS-II/BASS-II Test Matrix by PI Final.xlsx`; metadata folder | 129 BASS-II records and a six-sheet PI matrix. Fields include material, flow restriction/fan/air display, radiometer gain/frames, O2, CO2 and CO. | Material/flammability and condition-gap catalog. It has no same-format aerosol detector time series. |
| 5 | `BASS (ORIGINAL)/PSI-26_Experimental table_BASS.csv`; `BASS (ORIGINAL)/BASS test matrix.xlsx`; metadata folder | 122 BASS records; detailed as-run matrix, including material, ignition, flow and environment fields. | Historical material and experimental-condition context. |
| 6 | `FLEX/PSI-69_Experimental table_FLEX.csv`; `FLEX/20CAL08.txt`; metadata folder | 274 liquid-droplet records with fuel, pressure, ambient composition, initial/extinction diameter, burning rate, burn time/end. | A clean benchmark for gap-finding patterns and extinction questions; not SAME smoke data. |
| 7 | `ACME FLAME DESIGN/PSI-10_Experimental table_Flame Design_{Normal,Inverse Flame}.csv`; metadata folder | 207 normal + 120 inverse flame records; composition, flow, pressure, Zst and adiabatic temperature. | Catalog only, useful for combustion-condition coverage. |
| 8 | `ACME II/PSI-159_Experimental table_CFI-G_{Normal Flames,Inverse Flames}.csv`; metadata folder | 179 normal + 1,015 inverse records, with fuel, O2, pressure, burn rate/time, terminal state, temperature and comments. | Catalog/gap-finding source, not aerosol validation. |
| 9 | `SOFIE/*.pdf` | Four program/update/abstract documents; no machine-readable experiment table or raw time series in this folder. | Linkable future-work context only. |

### Formats, integrity and known risks

- The data are heterogeneous and analysis-ready only after a reproducible import layer: legacy `.xls`, `.xlsx`, CSV, narrative PDFs/docs/presentations and metadata text. Do not overwrite formulas or use Excel-rendered values as raw data.
- PSI-101 and PSI-102 are not a direct paired controlled study: different years, materials/conditions, instruments/processing conventions, and uneven run identifiers.
- Time bases include Unix-like seconds and formatted strings; runs can include duplicate seconds, multiple test/peak regions, setup/shutdown rows, and sentinel values such as `-10`.
- Data include duplicate/ambiguous candidates: PSI-101 `run63`/`run63a`, `run64`/`run64a`; PSI-102 has “peak 1/2,” averages and multi-run files. Preserve both until a deterministic selection rule is recorded.
- Raw detector values are voltages, not calibrated optical coefficients. PTrak/DustTrak may be zero over non-measurement periods. Unit labels and scaling differ by derived sheet.
- No universally clean lookup maps every raw workbook to an experimental-table row; automatic joins need confidence and an “unmatched/ambiguous” state.

## What each proposed module should be in the MVP

### 1. Deterministic coagulation: a transparent scenario engine

**Input:** user-selectable/material/run conditions; baseline window and observed PTrak/DustTrak/flow series when available. **Output:** a simulated number/mean-diameter trajectory plus an “observed versus scenario” panel.

Use a discrete sectional or moments implementation of the Smoluchowski equation. Start with Brownian kernel only; optionally gate residence time by documented flow/volume assumptions. Put every non-source parameter in an editable, cited assumptions panel: temperature, gas viscosity, particle density, initial count/diameter/lognormal width, sticking coefficient, chamber/transport volume and time step. Enforce nonnegative concentration and mass conservation checks.

It may say: “Under the selected assumptions, the model predicts …”. It may not say: “NASA measured coagulation caused …” without an independent validation target.

### 2. Optical scattering: measured signal first, physics second

**MVP measurement:** plot raw/detrended `ISSDetectorScatterMeasurement(Volts)` alongside obscuration, ion, PTrak and DustTrak signals over a declared test window. Report baseline, peak, AUC, time-to-peak and signal availability. Preserve source units.

**Optional calculated layer:** Rayleigh approximation only when particle diameter is safely much smaller than chosen wavelength; otherwise a Mie calculation requires user-provided wavelength and complex refractive index. Return relative/scaled scattering unless optical geometry/calibration is sourced. Treat detector scatter voltage as an optical-response proxy, not cross-section.

### 3. Experiment gap finding: catalog completeness, not fake recommendations

Construct a normalized study/run table with fields: investigation, source path, material/fuel, gravity/platform, geometry/flame type, O2, pressure, flow, duration, aging, outcome/measurement family, data level, and join confidence. Show coverage counts, missingness and duplicates. A gap is defensible only as “no usable record in the supplied corpus for [factor combination/measurement]”; rank it by explicit coverage rules, not an opaque ML score.

## Evidence-grounded scientific AI

Implement AI as a constrained answer layer over extracted records and document chunks:

1. Retrieve only project-source passages/rows plus the selected run output.
2. Require a source path, sheet/range or row ID for every numerical/scientific claim.
3. Return three sections: **Observed in source**, **Model result (assumptions named)** and **Unknown / needs experiment**.
4. Let the model formulate plain-language explanations, comparison summaries and suggested next measurements; do not let it execute unlogged calculations or invent citations.
5. Add deterministic checks: citation present, cited value matches source, unit displayed, no claim stronger than its evidence label, and a refusal for absent data.

## 36-hour implementation checklist

This leaves the last 2 hours as genuine integration/demo buffer; do not sacrifice it for an unvalidated fourth feature.

| Hours | Deliverable / checklist | Acceptance condition |
|---:|---|---|
| 0–2 | Freeze scope: SAME-R-first MVP; create repository, data-license/provenance note, source-path convention, and issue board. | App runs; source folder is read-only; no raw files copied into commits unless licensing permits. |
| 2–5 | Build `catalog` importer for the 10 CSVs and eight `i_Investigation.txt` files. Normalise exact source path, investigation ID/title, data level and measurement family. | Catalog displays 8 investigations and row counts above; no invented fields. |
| 5–9 | Build robust XLS/XLSX raw-run importer. Prefer raw/housekeeping sheet; parse headers; write one clean local derived table per source (run ID, material candidate, timestamp, 98 raw columns, source hash/path). | Import at least 3 PSI-101 and 3 PSI-102 representative files; record failures, sheet selected, row count and schema version. |
| 9–11 | Implement run browser, raw/derived-sheet toggle and QA panel: timestamps, missingness, sentinel count, duplicate times, scaling/formula warning, join confidence. | A user can select a source file and see no hidden transformations. |
| 11–14 | Add event-window workflow: default baseline/preheat/test/cooldown proposal from state signals; user-confirmed bounds; save deterministic metrics (baseline, peak, AUC, peak time). | Metrics reproduce from saved window configuration. |
| 14–18 | Build scattering module MVP: aligned raw signals; units; baseline correction option; peak/AUC summaries; CSV/PNG export. | Demo one PSI-101 run and one PSI-102 run without claiming calibration. |
| 18–22 | Implement coagulation scenario engine: sectional/moment solver, Brownian kernel, controls, conservation/nonnegative tests, assumption panel and overlay. | Same inputs reproduce same curve; invalid/missing inputs visibly block calculation. |
| 22–25 | Build gap matrix from catalog and experimental CSVs. Include coverage by investigation/material/measurement family and explicit unknowns. | Clicking a cell opens source records; “no records” means no usable imported record. |
| 25–28 | Add grounded AI: retrieval payloads, claim/evidence/unknown response contract, citations to source path/sheet/row, and refusal tests. | 10 scripted questions: every factual answer cites a source; unsupported questions return unknown. |
| 28–31 | Add investigation ranking/catalog UI: relevance score is a published rubric (direct aerosol raw data, condition metadata, scale/context, machine readability), not an AI judgment. | SAME-R first, SAME second, and the ranks above are explainable from fields. |
| 31–33 | Scientific/engineering QA: inspect 10 runs, compare source headers/time counts, check derived scaling, window boundaries, model conservation and catalog counts. | Defects are fixed or shown as warnings; no silent fallback to zero. |
| 33–34 | Usability pass: loading/errors, units, assumptions, source links, empty states, screenshots. | A judge can reach a cited conclusion in under two minutes. |
| 34–36 | Rehearse demo, record evidence-backed narration, package README/architecture/data dictionary and a “known limits” slide. | Offline demo works; every shown result has a source or assumption label. |

## Do not build in 36 hours

- A learned causal/coagulation predictor trained on these heterogeneous raw workbooks.
- Universal particle sizing, Mie inversion or detector-alarm certification.
- Automated TEM/image analysis: the folder does not contain the actual SAME TEM/image corpus required for it.
- Cross-investigation numerical pooling without harmonized variables, calibration and experimental design.
- A chatbot that answers without citations.

## Recommended judging story

“AERO-PSI turns difficult NASA combustion archives into an auditable experiment navigator. It shows what a smoke run actually measured, separates a declared coagulation/scattering scenario from observation, identifies uncovered conditions, and explains every conclusion with a source link or an explicit unknown.”
