#!/bin/sh
set -eu
exec python -m aero_psi serve --host 0.0.0.0 --port "${PORT:-8080}"
