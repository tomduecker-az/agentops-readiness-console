#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d "services/api/.venv" ]; then
  echo "ERROR: services/api/.venv not found."
  echo "Create it first and install requirements."
  exit 1
fi

source services/api/.venv/bin/activate

export PYTHONPATH="services/api:packages/workflow_core:packages/readiness_core:packages/audit_core:packages/policy_core:packages/project_mgmt_core"

echo ""
echo "Starting AI Workflow Assessment local app..."
echo "Open: http://127.0.0.1:8000"
echo ""

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
