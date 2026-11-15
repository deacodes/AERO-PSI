# AERO-PSI Cloud Run

The Python service serves both the frontend and API. Scientific data is downloaded
from `aeropsi-data` into a checksum-verified, ephemeral cache at each new instance.
Investigations stay in browser IndexedDB. The production URL has a separate
browser library from localhost; export local work before switching origins.

## Existing infrastructure

- Region: `asia-south1`
- Service / Artifact Registry repository: `aeropsi`
- Runtime account: `aeropsi-runtime` (Vertex AI User; Object Viewer on the data bucket)
- Build account: `aeropsi-builder` (Log Writer; repository Writer; build-source bucket Viewer)
- Private build-source bucket: `<project-id>-aeropsi-builds` (7-day object lifecycle)
- Initial hosting: zero minimum instances, one maximum instance, 1 CPU, 2 GiB RAM,
  two simultaneous requests, 300-second request timeout, 240-second startup probe.
  These limits are not a spending cap. Vertex usage is billed separately.

## Update

With project ADC available, run:

```sh
.venv/bin/python tools/deploy_cloud_run.py \
  --project YOUR_PROJECT_ID --model YOUR_WORKING_VERTEX_MODEL \
  --vertex-location global --public --apply
```

Omit `--apply` to inspect the strict upload allowlist first. This script uses the
Google APIs directly; no local Docker or gcloud installation is required. It builds
in Cloud Build and records build/image/URL in ignored `output/deployment/latest.json`.
It preserves unrelated IAM bindings when granting public invocation. Without
`--public`, it does not add public access (nor revoke previously granted access).

The package contains only application Python, frontend assets, mappings, dependency
files, Dockerfile and startup script. It excludes credentials, `.env`, local NASA
data, derived products, exports, investigations, virtual environments and Git history.
Cloud Run uses its service account's ADC. Do not upload local credential files.

## Verify

```sh
AERO_PSI_TEST_URL=https://YOUR_SERVICE_URL \
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
node tests/browser_private_storage.cjs
```

Also check `/api/v1/health`, Mie scattering, a real source table, a short SI question
and a gap review. Browser tests require Playwright. Live SI checks incur model usage.

Each new instance currently fetches about 761 MB before serving requests. This
cache consumes instance memory; keep enough headroom for calculations. Source
files remain private in Cloud Storage. Do not delete local originals as part of deployment.
