#!/usr/bin/env bash
# One-time local setup. Safe to re-run - every step here is idempotent.
#
# What this does:
#   1. Checks Docker and Docker Compose are installed and on PATH.
#   2. Creates .env from .env.example if .env doesn't exist yet.
#   3. Opens up write permissions on data/ and dbt/ so the Airflow
#      container (which runs as a different, non-root user than your host
#      user) can write generated files and dbt's own target/logs dirs into
#      these bind-mounted directories. See README "Known limitations" for
#      why this is a chmod 777 rather than something more surgical.
#
# Requires a Unix-like shell: works as-is on Linux and macOS. On Windows,
# run this from a WSL2 terminal (not PowerShell) - see README for the
# Windows setup path.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> Checking for Docker..."
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: 'docker' command not found. Install Docker Desktop (Windows/macOS)"
    echo "       or Docker Engine (Linux) before continuing. See README for details."
    exit 1
fi

echo "==> Checking for Docker Compose..."
if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: 'docker compose' command not found or not working."
    echo "       Docker Compose v2 ships with recent Docker Desktop installs;"
    echo "       on Linux you may need to install the compose plugin separately."
    exit 1
fi

echo "==> Setting up .env..."
if [ -f .env ]; then
    echo "    .env already exists, leaving it untouched."
else
    cp .env.example .env
    echo "    Created .env from .env.example (safe defaults, no changes needed)."
fi

echo "==> Fixing permissions on data/ and dbt/..."
echo "    (Airflow's container user can't write into these bind-mounted"
echo "    directories otherwise - see README for why.)"
CHMOD_LOG="$(mktemp)"
chmod -R 777 data/ dbt/ 2>"$CHMOD_LOG" || true
if [ -s "$CHMOD_LOG" ]; then
    echo "    Note: some files couldn't have their permissions changed - this"
    echo "    happens if Airflow (running as a different user inside its"
    echo "    container) already created them, e.g. dbt/target/*.json from a"
    echo "    previous 'dbt run' triggered through the DAG. If Airflow tasks"
    echo "    later fail with PermissionError, re-run this step with sudo:"
    echo "        sudo chmod -R 777 data/ dbt/"
fi
rm -f "$CHMOD_LOG"

echo ""
echo "Setup complete. Next steps:"
echo "  1. docker compose up -d"
echo "  2. Wait for all three services to become healthy: docker compose ps"
echo "  3. Airflow UI:   http://localhost:8080  (see README for the admin password)"
echo "  4. Superset UI:  http://localhost:8088  (login: admin / admin)"
echo "  5. In Airflow, unpause and trigger the 'fintech_pipeline' DAG."
