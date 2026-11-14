# AERO-PSI data dictionary

## Data layers

| Layer | Status | Location | Meaning |
|---|---|---|---|
| NASA source archive | Present | `DATA/` | Original local files. Read only. |
| Source catalog | Present | `aero_psi_catalog.json` | Generated inventory of source files, investigation metadata, and CSV-table summaries. |
| Normalized run metadata | Planned | `derived/run_metadata.*` | One record per imported raw/derived run workbook. |
| Normalized time series | Planned | `derived/timeseries/` | Source-preserving sampled measurements and device-state fields. |
| Windowed observed metrics | Planned | `derived/metrics.*` | Explicitly windowed baseline/peak/AUC metrics. |
| Scenario results | Planned | `derived/scenarios/` | Deterministic model outputs and assumption sets. |

## Source catalog: `aero_psi_catalog.json`

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Catalog schema version. |
| `generated_at` | ISO 8601 string | Catalog creation time in UTC. |
| `data_root` | string | Local source archive used during indexing; do not display publicly by default. |
| `read_only_source` | boolean | Confirms catalog generation does not modify the archive. |
| `value_state_vocabulary` | array | Supported source/derived field states: observed, missing, unknown, not applicable, and ambiguous. |
| `summary.file_count` | integer | Number of non-system source files indexed. |
| `summary.format_counts` | object | Source file count grouped by extension. |
| `investigations[]` | array | Metadata parsed from each `i_Investigation.txt` source. |
| `csv_tables[]` | array | Schema, row count, material counts, and a development preview for each source CSV. |
| `files[]` | array | One indexed record per source file. |

## Source-file record: `files[]`

| Field | Type | Meaning / rule |
|---|---|---|
| `source_path` | string | Relative path below `DATA/`; canonical provenance key. |
| `investigation_group` | string | Top-level source folder, such as `PSI101` or `SAFFIRE`. |
| `format` | string | Lowercase source extension without `.`. |
| `bytes` | integer | File size in bytes at indexing time. |
| `file_role` | string | Catalog classification, not a scientific claim. |
| `material_candidate` | string or null | Filename-based material candidate; requires verification for analysis. |
| `run_id_candidate` | string or null | Filename-derived run/test candidate; not a verified join key. |
| `measurement_family` | string | High-level study category for navigation/filtering. |

## Investigation record: `investigations[]`

| Field | Source |
|---|---|
| `source_path` | Metadata-file relative path. |
| `group` | Top-level source folder. |
| `investigation_id` | `Study Identifier` in source metadata. |
| `title` | `Study Title` in source metadata. |
| `acronym` | `Comment[Investigation Acronym]` in source metadata. |
| `platform` | `Comment[Flight Platform]` in source metadata. |
| `research_area` / `subresearch_area` | Corresponding source metadata fields. |
| `objective` | Source objective; context, not extracted measurements. |

## Source CSV summary: `csv_tables[]`

| Field | Meaning |
|---|---|
| `source_path` | Source CSV relative path. |
| `row_count` | Data-record count, excluding the header. |
| `columns` | Original CSV headers, preserved exactly. |
| `material_column` | Best matching material/fuel/sample-type column. |
| `material_counts` | Non-empty values observed in that material column. |
| `preview` | First three rows for development inspection only. |

## Planned normalized run metadata

No normalized run dataset exists yet. Every imported record must include `run_key`, `source_path`, `source_sha256`, `worksheet_name`, `source_row_count`, `parser_version`, `material`, `run_id`, `join_status` (`verified`, `candidate`, `ambiguous`, or `unmatched`), and `warnings`.

## Core planned time-series fields

| Normalized alias | Source header example | Unit / interpretation |
|---|---|---|
| `timestamp_text` | `TimeString` | Original formatted timestamp text. |
| `timestamp_source` | `Time` | Original numeric time; conversion rule recorded separately. |
| `run_mode` | `RunMode` | Instrument/run state. |
| `test_number` | `TestNumber` | Source test identifier. |
| `elapsed_test_seconds` | `ElapsedTestTime(Secs)` | Seconds, source-provided. |
| `plume_temperature_c` | `GasPlumeTemperature(DegC)` | Degrees Celsius. |
| `obscuration_voltage` | `ISSDetectorObscurationMeasurement(Volts)` | Detector signal in volts. |
| `scatter_voltage` | `ISSDetectorScatterMeasurement(Volts)` | Detector signal in volts, not optical cross-section. |
| `sts_voltage` | `STSDetectorMeasurement(Volts)` | Detector signal in volts. |
| `ion_a_voltage` / `ion_b_voltage` | `IonDetectorA/BMeasurement(Volts)` | Detector signals in volts. |
| `ptrak_particles_per_cc` | `PTrakMeasurement(PtPerCC)` | Particles per cubic centimetre when source is in raw scale. |
| `dusttrak_a_mg_m3` / `dusttrak_b_mg_m3` | `DustTrakA/BMeasurement(MgPerM3)` | Milligrams per cubic metre. |
| `lfe_flow_sccm` | `LFEFlowRate[AT08](SCCM)` | Standard cubic centimetres per minute. |
| `mfc_flow_lpm` | `MFCMassFlowRate(LPM)` | Litres per minute. |

Derived graph sheets may invert polarity, reset time, or rescale PTrak. A raw-to-derived transformation must never be assumed: it needs a recorded formula and a separate display field.

## Evidence labels

| Label | Meaning |
|---|---|
| Observed in source | A source value with a direct provenance link. |
| Model result | Deterministic output with formula/version and all inputs retained. |
| Assumption | A non-source input selected by a user or app default. |
| Unknown / needs data | A value, calibration, or relationship not established by the archive. |

