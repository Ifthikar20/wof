#!/usr/bin/env bash
# Run the whole app locally with nothing but Python 3.11+ and Node 20+.
#
#   ./scripts/dev.sh            start backend (http://127.0.0.1:8000) + frontend (http://localhost:3000)
#   ./scripts/dev.sh --reset    wipe local data first (database, uploads, captured emails)
#   ./scripts/dev.sh --seed     load demo founders and stories (also done automatically on first run)
#
# Uses wof.settings.local: SQLite, in-memory cache, inline background jobs, emails written to
# backend/.local/mail, images stored in backend/.local/media. See docs/10 for the Docker stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
export DJANGO_SETTINGS_MODULE=wof.settings.local
export NEXT_TELEMETRY_DISABLED=1
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
export SITE_URL="${SITE_URL:-http://localhost:3000}"

RESET=0; SEED=0
for arg in "$@"; do
  case "$arg" in
    --reset) RESET=1 ;;
    --seed) SEED=1 ;;
    -h|--help) sed -n 2,10p "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
die() { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# ---- prerequisites --------------------------------------------------------------------------
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null || die "python3 not found (need 3.11+)"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || die "Python 3.11+ required (found $("$PY" --version))"
command -v node >/dev/null || die "node not found (need 20+)"
node -e 'process.exit(parseInt(process.versions.node) >= 20 ? 0 : 1)' || die "Node 20+ required (found $(node --version))"
command -v npm >/dev/null || die "npm not found"

# ---- backend --------------------------------------------------------------------------------
if [ "$RESET" = 1 ] && [ -d "$BACKEND/.local" ]; then
  say "Removing local data (database, media, mail)"
  rm -rf "$BACKEND/.local"
fi

if [ ! -x "$VENV/bin/python" ]; then
  say "Creating Python virtualenv"
  "$PY" -m venv "$VENV"
fi
if [ ! -f "$VENV/.installed" ] || [ "$BACKEND/requirements-dev.txt" -nt "$VENV/.installed" ]; then
  say "Installing backend dependencies"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -r "$BACKEND/requirements-dev.txt"
  touch "$VENV/.installed"
fi

FIRST_RUN=0
[ -f "$BACKEND/.local/db.sqlite3" ] || FIRST_RUN=1
say "Applying database migrations"
(cd "$BACKEND" && "$VENV/bin/python" manage.py migrate --noinput -v 0)
if [ "$FIRST_RUN" = 1 ] || [ "$SEED" = 1 ]; then
  say "Loading demo founders and stories"
  (cd "$BACKEND" && "$VENV/bin/python" manage.py seed_demo)
fi

# ---- frontend -------------------------------------------------------------------------------
if [ ! -d "$FRONTEND/node_modules" ] || [ "$FRONTEND/package-lock.json" -nt "$FRONTEND/node_modules/.package-lock.json" ]; then
  say "Installing frontend dependencies"
  (cd "$FRONTEND" && npm ci --no-fund --no-audit)
fi

# ---- run both ---------------------------------------------------------------------------------
PIDS=()
cleanup() {
  trap - INT TERM EXIT
  # Stop only what we started (and their children), never the caller's process group.
  for pid in "${PIDS[@]}"; do
    pkill -TERM -P "$pid" 2>/dev/null || true
    kill -TERM "$pid" 2>/dev/null || true
  done
}
trap cleanup INT TERM EXIT

say "Starting API on http://127.0.0.1:8000"
(cd "$BACKEND" && exec "$VENV/bin/python" manage.py runserver 127.0.0.1:8000) &
PIDS+=($!)

say "Starting web app on http://localhost:3000"
(cd "$FRONTEND" && exec npx next dev -p 3000) &
PIDS+=($!)

sleep 2
cat <<EOF

  Wall of Founders is running locally.

    Web app       http://localhost:3000
    Admin         http://127.0.0.1:8000/admin/   (admin@wof.local / admin-demo-password)
    Demo founder  maya@solarloop.energy / demo-password-please-change
    Emails        backend/.local/mail/           (verification links, digests, resets)
    Scheduled     cd backend && .venv/bin/python manage.py run_periodic

  Press Ctrl-C to stop both servers.

EOF
wait
