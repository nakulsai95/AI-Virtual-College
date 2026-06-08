#!/usr/bin/env bash
# Boot the AULA backend (FastAPI). Usage: ./run.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
