#!/usr/bin/env bash
# Start Canistra ICP Hosting — backend (FastAPI) + frontend (Next.js)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""
DFX_STARTED=0
START_DFX=0

usage() {
  cat <<'EOF'
Usage: ./start.sh [options]

Options:
  --local-dfx   Start local dfx replica (needed when DEPLOY_NETWORK=local)
  --help        Show this help

URLs when running:
  Frontend  http://localhost:3000
  Backend   http://localhost:8000
  API docs  http://localhost:8000/docs
EOF
}

for arg in "$@"; do
  case "$arg" in
    --local-dfx) START_DFX=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

cleanup() {
  echo ""
  echo "Stopping services..."
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  if [[ "$DFX_STARTED" -eq 1 ]]; then
    dfx stop 2>/dev/null || true
  fi
  wait 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "==================================="
echo " Canistra ICP Hosting — dev stack"
echo "==================================="
echo ""

# --- Prerequisites ---
if [[ ! -f "$ROOT/backend/.env" ]]; then
  echo "Missing backend/.env — copy from backend/.env.example and configure it:"
  echo "  cp backend/.env.example backend/.env"
  exit 1
fi

if [[ ! -d "$ROOT/backend/.venv" ]]; then
  echo "Missing backend/.venv — create the virtualenv first:"
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
  exit 1
fi

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$ROOT/frontend" && npm install)
fi

if [[ "$START_DFX" -eq 1 ]]; then
  if command -v dfx >/dev/null 2>&1; then
    echo "Starting dfx local replica..."
    export DFX_WARNING=-mainnet_plaintext_identity
    dfx start --background 2>/dev/null || true
    DFX_STARTED=1
    sleep 2
    echo "✓ dfx replica (http://localhost:4943)"
  else
    echo "Warning: dfx not found — skip --local-dfx or install dfx"
  fi
fi

# --- Backend ---
echo "Starting backend on http://localhost:8000 ..."
(
  cd "$ROOT/backend"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  exec python run.py
) &
BACKEND_PID=$!

# Wait for API
for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:8000/docs" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

# --- Frontend ---
echo "Starting frontend on http://localhost:3000 ..."
(
  cd "$ROOT/frontend"
  exec npm run dev
) &
FRONTEND_PID=$!

echo ""
echo "✓ Frontend   http://localhost:3000"
echo "✓ Backend    http://localhost:8000"
echo "✓ API docs   http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."
echo ""

wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || wait
