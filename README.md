# AERO-PSI

AERO-PSI is an interactive, evidence-grounded explorer for NASA spacecraft-fire and smoke-aerosol investigations. It will let users inspect source-backed detector time series, test clearly labelled coagulation scenarios, compare optical-response signals, identify data-coverage gaps, and receive explanations that distinguish observations from assumptions.

## Current status

The read-only NASA source archive is in `DATA/`. The platform includes imported detector time series, coagulation and spherical scattering scenarios, question-specific ranking, measurement planning, and scientific AI. Experimental validation remains separate from numerical checks.

## Run locally

Requirements: Python 3.11 or newer. Use the project environment for scientific libraries and Vertex AI. CLI startup automatically selects `.venv` when present; it does not install packages. For a fresh checkout, create `.venv` and install `requirements.txt` into it before starting.

```bash
python3 -m aero_psi index
python3 -m aero_psi serve
```

Then open `http://127.0.0.1:8000` for the local web shell. Its versioned API lives at `http://127.0.0.1:8000/api/v1/health`, `/api/v1/investigations`, and `/api/v1/summary`.

## Evidence policy

- **Observed in source:** a NASA source value with source path and row/sheet reference.
- **Model result:** a deterministic calculation with inputs and version recorded.
- **Assumption:** a user-selected or default parameter not supplied by the source record.
- **Unknown / needs data:** a requested value or relationship the supplied archive cannot establish.

The project does not treat raw detector voltage as a calibrated optical property, infer particle size where it was not measured, or claim causation from co-varying signals.

## Repository layout

| Path | Purpose |
|---|---|
| `DATA/` | Immutable local NASA source archive; excluded from Git by default. |
| `aero_psi/` | Python package: backend, scientific models, evidence and SI workflows. |
| `tools/` | Data packaging and document-review utilities. |
| `tests/` | Python regression tests and browser checks. |
| `aero_psi_catalog.json` | Generated local catalog; rebuild with `index`. |
| [DATA_DICTIONARY.md](markdowns/DATA_DICTIONARY.md) | Dataset/field definitions and provenance rules. |
| [DATA_POLICY.md](markdowns/DATA_POLICY.md) | Attribution, redistribution, and source-handling policy. |
| [PROJECT_CHECKLIST.md](markdowns/PROJECT_CHECKLIST.md) | Full build checklist and MVP cut line. |

Do not edit, rename, or generate files inside `DATA/`. Derived tables, temporary conversions, and caches belong outside that archive.


### Expanded backend environment

The optical model requires the pinned dependencies in `requirements.txt`. Use the project environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m aero_psi serve
```

Example optical requests are in `examples/scattering.json` and `examples/coupled_optics.json`. The model lab now exposes gravity and gas controls, a size-distribution timeline, observed-window analysis and angular scattering. Evidence SI can plan and execute bounded investigations and export their records. Advanced calibration/uncertainty forms remain API-only.

## Browser-private investigations and cloud data

Studio work is saved in IndexedDB for the current browser and website origin. The public backend does not list or reopen server-side investigations. Existing local `derived/studio/` and `derived/investigations/` files are left untouched and are not migrated into visitor libraries. Calculations and SI send the relevant browser record to the backend for request-scoped processing; no shared copy is saved. Browser data can be lost when site storage is cleared or a private-browsing session ends. Export important work; exports currently have no in-app import flow. Changing hostname or port creates a separate browser library.

For scientific runtime data, set `AERO_PSI_STORAGE_BUCKET=aeropsi-data` in `.env` or the hosting environment and run `python3 -m aero_psi serve`. Authentication uses ADC locally and the service identity when deployed. Grant the runtime identity read-only object access to the bucket. The app downloads the allowed scientific objects into `cache/cloud-runtime/<bucket>/` by default, verifies SHA-256 and file sizes, and reuses unchanged files. Override `AERO_PSI_CLOUD_CACHE` to locate this disposable cache elsewhere. The first startup downloads about 761 MB; allow time, disk capacity and applicable download charges. This is a cached snapshot at startup, not a network filesystem mount or a live write-through connection. Restart after updating bucket data. Failed authentication or checksum validation stops startup rather than silently falling back to different data.

Unset the bucket setting (or explicitly set it to an empty string) to use project-local scientific files. Code, mappings, secrets and visitor investigations are never downloaded from this data bucket. Do not delete your originals until you have a separate backup and have verified the deployed workflow.
