# AERO-PSI

AERO-PSI is an interactive, evidence-grounded explorer for NASA spacecraft-fire and smoke-aerosol investigations. It will let users inspect source-backed detector time series, test clearly labelled coagulation scenarios, compare optical-response signals, identify data-coverage gaps, and receive explanations that distinguish observations from assumptions.

## Current status

The read-only NASA source archive is in `DATA/`. The platform includes imported detector time series, coagulation and spherical scattering scenarios, question-specific ranking, measurement planning, and scientific AI. Experimental validation remains separate from numerical checks.

## Run locally

Requirements: Python 3.11 or newer. Use the project environment for scientific libraries and Vertex AI. CLI startup automatically selects `.venv` when present; it does not install packages. For a fresh checkout, create `.venv` and install `requirements.txt` into it before starting.

```bash
python3 aero_psi_backend.py index
python3 aero_psi_backend.py serve
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
| `aero_psi_backend.py` | Read-only source-catalog builder and local JSON API. |
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
.venv/bin/python aero_psi_backend.py serve
```

Example optical requests are in `examples/scattering.json` and `examples/coupled_optics.json`. The model lab now exposes gravity and gas controls, a size-distribution timeline, observed-window analysis and angular scattering. Evidence SI can plan and execute bounded investigations and export their records. Advanced calibration/uncertainty forms remain API-only.
