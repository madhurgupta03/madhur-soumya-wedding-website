#!/usr/bin/env bash
# Start the hot-reload server and open the site in the default browser.
cd "$(dirname "$0")" || exit 1
PORT="${1:-8000}"
(sleep 1 && open "http://localhost:$PORT") &
exec python3 serve.py "$PORT"
