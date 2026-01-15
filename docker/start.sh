#!/bin/bash
set -euo pipefail

# ensure db directory exists
DB_DIR="/app/db"
mkdir -p "$DB_DIR"
DB_FILE="$DB_DIR/verification.db"
if [ ! -f "$DB_FILE" ]; then
  echo "Creating SQLite database at $DB_FILE"
  sqlite3 "$DB_FILE" "VACUUM;" >/dev/null 2>&1 || true
fi

export DATABASE_TYPE="sqlite"
export DATABASE_LOCATION="$DB_FILE"

cd /app/server

python -m app.bot &
BOT_PID=$!

uvicorn app.main:app --host 0.0.0.0 --port 5000 &
API_PID=$!

cd /app/client
python -m http.server 8000 --bind 0.0.0.0 &
WEB_PID=$!

cleanup() {
  echo "Stopping services"
  kill "$BOT_PID" "$API_PID" "$WEB_PID" 2>/dev/null || true
  wait "$BOT_PID" "$API_PID" "$WEB_PID" 2>/dev/null || true
}

trap cleanup SIGINT SIGTERM

wait -n
EXIT_CODE=$?
cleanup
exit $EXIT_CODE
