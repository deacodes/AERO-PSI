# AERO-PSI

An interactive platform for **aerosol coagulation, multi-angle scattering and experiment gap finding**, supported by NASA source data and scientific AI.

**Public website:** https://aeropsi-4p4a2ghj4a-el.a.run.app

## What the platform does

- **NASA archive:** browse experiment tables, imported run signals and supporting documents, with descriptive titles, type tags and original filenames. Inspect source rows and provenance.
- **Coagulation:** explore sectional particle-population scenarios with Brownian and differential-settling physics, gas conditions, prescribed sources/losses, distributions and conservation diagnostics.
- **Scattering:** calculate spherical Mie or applicable Rayleigh scattering, including scenarios coupled to a computed coagulation distribution. Outputs are theoretical optical quantities, not measured detector voltages.
- **Gap finder:** review a research question against selected investigations, inspect available measurements and identify unresolved prerequisites. SI review and the basic evidence check are distinct modes.
- **Scientific intelligence:** discuss general science, selected evidence or model results. Table discussions use computed worksheet summaries and small inline plots, with source-row references, missing/sentinel counts and operating-state diagnostics. Follow-ups retain the selected context.
- **Investigation Studio:** create and revise studies, attach evidence and calculated results, track steps and export records. Work is private to the current browser.

The frontend uses HTML, CSS and JavaScript; the backend is Python with a standard-library HTTP server. Vertex AI supplies scientific explanations. This is an experimental research tool: numerical checks and source citations do not constitute experimental validation or independent verification of every AI claim.

## Repository structure

| Path | Purpose |
|---|---|
| `aero_psi/` | Python package: HTTP API, models, ingestion, evidence, SI, browser-record processing and cloud runtime loading. |
| `frontend/pages/` | Separate HTML page templates. |
| `frontend/js/` | Page controllers, graph rendering, browser storage and SI discussions. |
| `frontend/styles/` | Shared and page-specific CSS, themes and reduced-motion support. |
| `frontend/components/`, `frontend/assets/`, `frontend/vendor/` | Shared UI, images and bundled third-party assets. |
| `mappings/` | Source-linked scientific notes, verified run links and display labels. |
| `mappings/source_labels.json` | Editable human-readable titles and type tags, keyed by the **unchanged original source path**. |
| `tools/` | Data packaging/upload, source-review utilities and Cloud Run deployment script. |
| `tests/` | Scientific/API regression tests and Playwright browser checks. |
| `examples/` | Example model request payloads. |
| `deploy/` | Container startup script and [deployment instructions](deploy/README.md). |
| `Dockerfile`, `.dockerignore`, `.gcloudignore` | Container packaging and strict build-upload exclusions. |
| `requirements.txt` | Core scientific and Vertex dependencies. |
| `requirements-deploy.txt` | Versions used by the deployed Python 3.13 container. |
| `markdowns/` | Scientific notes, data policy, dictionaries and project checklists. |
| `DATA/` | Original NASA files; local/private runtime data, excluded from Git. |
| `derived/`, `aero_psi_catalog.json` | Imported tables, evidence excerpts and catalog; excluded from Git. |
| `cache/`, `output/`, `exports/` | Disposable runtime cache, generated reports and local exports; excluded from Git. |
| `.env`, `.venv/`, `__pycache__/` | Local configuration, environment and bytecode; excluded from Git. |

Titles and tags are presentation metadata, not new scientific claims. They do not rename files or change source IDs, checksums, measurement units or run joins. Unknown or ambiguous run identities must not be invented. New sources fall back to a readable filename until a label is added.

## Run locally

Python 3.13 is recommended to match deployment. Create an environment first:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-deploy.txt
cp .env.example .env
```

Edit the project, Vertex location and working model settings in `.env`. Authentication uses Google **Application Default Credentials (ADC)**; do not put credential JSON or secrets in Git. A fresh checkout does not contain the private scientific runtime data.

Choose one data source:

1. **Cloud bucket:** set `AERO_PSI_STORAGE_BUCKET=aeropsi-data`. Your ADC identity needs read access to that bucket and Vertex permissions for SI. Cloud Run uses its attached service account instead of local credentials.
2. **Local files:** set `AERO_PSI_STORAGE_BUCKET=` and supply `DATA/`, `aero_psi_catalog.json` and the required `derived/` data. `python -m aero_psi index` rebuilds the catalog from local sources; it does **not** perform all ingestion or document extraction.

Start the app:

```sh
.venv/bin/python -m aero_psi serve
```

Open http://127.0.0.1:8000. The health endpoint is `/api/v1/health`. CLI startup selects `.venv` automatically when present; it does not install missing packages. Set `AERO_PSI_COPILOT_ENABLED=false` when testing without live AI calls.

## Cloud data and deployment

Cloud Run hosts the frontend and API together. Cloud Storage holds the allowlisted scientific runtime: `DATA/`, `aero_psi_catalog.json`, `derived/timeseries/`, `derived/evidence/` and the ingestion manifest. It does not hold visitor investigations, `.env` or local credentials.

At startup, the app downloads and verifies the scientific snapshot by size and SHA-256. The current archive is about 761 MB. Unchanged cached objects are reused; a fresh Cloud Run instance must fetch its own cache. Local cache defaults to `cache/cloud-runtime/<bucket>/`; the container uses `/tmp/aeropsi-runtime`. Override `AERO_PSI_CLOUD_CACHE` if needed. This is a startup snapshot, not a live filesystem mount. Restart after updating bucket data. Authentication or checksum failures stop startup rather than silently selecting other data.

See [deploy/README.md](deploy/README.md) for build, deployment and verification commands. The deployment helper uploads only application code, mappings and frontend assets; local Docker is not required. Deploying local files does not commit or push them to GitHub. Hosting and Vertex usage can incur charges; instance limits are not a spending cap.

## Private investigations

Studio saves to **IndexedDB in the visitor's browser**, scoped to the website origin. Other visitors cannot list or reopen that work through the backend. Relevant records are sent for request-scoped calculations or SI processing, without saving a shared server-side investigation.

Export important studies. Clearing site storage, ending a private-browsing session or changing browser/device can remove access. Localhost and the public website have separate libraries. There is currently no cross-device synchronization or in-app export import flow. Existing local `derived/studio/` and `derived/investigations/` files are not automatically migrated or published.

## Verification

```sh
.venv/bin/python -m unittest discover -s tests
```

Browser checks require Node.js, Playwright and a browser. For example, with the app running:

```sh
AERO_PSI_TEST_URL=http://127.0.0.1:8000 \
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
node tests/browser_private_storage.cjs
```

Model request examples include `examples/scattering.json` and `examples/coupled_optics.json`. Live SI checks use the configured cloud model and can incur usage.

## Scientific boundaries

- **Observed values** retain source paths, rows and worksheet references. Labels and file tags do not certify calibration or data quality.
- **Calculated patterns** are descriptive: extrema, adjacent changes or correlated signals do not establish a causal mechanism. Inline graphs preserve gaps and distinguish sampled plot points from full-row statistics.
- **Model results** retain scenario assumptions and numerical diagnostics; they are not automatically fitted to or validated against NASA runs.
- **AI explanations** distinguish observations from possible mechanisms, but citation identity checks do not independently verify every claim.
- **Archive gaps** describe supplied evidence, not proof that a measurement is absent from all scientific literature.

Do not modify or generate files inside `DATA/`. Keep source originals intact and write derived products elsewhere. See [data policy](markdowns/DATA_POLICY.md), [data dictionary](markdowns/DATA_DICTIONARY.md) and [project checklist](markdowns/PROJECT_CHECKLIST.md).
