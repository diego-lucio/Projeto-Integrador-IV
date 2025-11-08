#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

# Wait for MySQL to be reachable if running in compose
HOST=${DB_HOST:-mysql}
PORT=${DB_PORT:-3306}

echo "Waiting for database ${HOST}:${PORT}..."
for i in $(seq 1 60); do
  if nc -z "${HOST}" "${PORT}" >/dev/null 2>&1; then
    echo "Database is up."
    break
  fi
  echo "Waiting... ($i/60)"
  sleep 2
done

# Run once or every N minutes
if [ -n "${ETL_INTERVAL_MINUTES:-}" ]; then
  echo "Running ETL every ${ETL_INTERVAL_MINUTES} minutes..."
  while true; do
    python /app/pipeline.py || true
    sleep "$(( ETL_INTERVAL_MINUTES * 60 ))"
  done
else
  echo "Running ETL once..."
  python /app/pipeline.py
fi
