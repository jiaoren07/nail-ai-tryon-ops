#!/bin/sh
# Container entrypoint (Dockerfile CMD).
#
# Free container tiers give each cold start a fresh ephemeral filesystem,
# so the database is normally absent here. Seeding at start therefore does
# double duty: it builds the demo data AND re-anchors the rolling time
# windows (trending 24h / cold 7d / overview today-vs-yesterday) to "now",
# which is exactly the manual reseed step a local demo needs daily.
set -e

cd "$(dirname "$0")/.."

if [ ! -f nail_demo.db ]; then
  echo "[start] no database found — seeding demo data"
  python -X utf8 scripts/seed_all.py
else
  echo "[start] database present — skipping seed"
fi

# Hosts inject the port to listen on; default keeps local `sh scripts/start.sh` working.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
