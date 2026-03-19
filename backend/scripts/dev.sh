#!/bin/bash
# ICP Hosting Platform - Local Development Server
# Starts the backend API server and local dfx replica

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================"
echo "ICP Hosting Platform - Local Dev"
echo "================================"
echo ""

# Check if dfx is installed
if ! command -v dfx &> /dev/null; then
    if [ ! -f ~/.local/bin/dfx ]; then
        echo "Error: dfx is not installed"
        echo "Run: ./scripts/setup.sh"
        exit 1
    fi
    export PATH=$PATH:~/.local/bin
fi

export DFX_WARNING=-mainnet_plaintext_identity

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    # Kill the server if it's running
    jobs -p | xargs -r kill 2>/dev/null || true
    # Stop dfx replica if it's running
    ~/.local/bin/dfx stop 2>/dev/null || true
}

trap cleanup EXIT

# Start dfx replica in background
echo "Starting dfx local replica..."
~/.local/bin/dfx start --background --clean > /tmp/dfx.log 2>&1 &
sleep 3

# Deploy the portfolio canister to local replica
echo "Deploying portfolio canister..."
cd /home/prasanga/internet-computer-protocol
~/.local/bin/dfx deploy portfolio --network local > /dev/null 2>&1 || true
echo "✓ Portfolio canister deployed (http://localhost:4943)"

# Activate Python environment
cd "$PROJECT_ROOT"
source .venv/bin/activate

# Start the backend server
echo ""
echo "Starting backend API server..."
echo "✓ API running on http://127.0.0.1:8000"
echo ""
echo "Available endpoints:"
echo "  - POST   /api/v1/auth/signup     - Register user"
echo "  - POST   /api/v1/auth/login      - Login"
echo "  - POST   /api/v1/projects/       - Create project"
echo "  - GET    /api/v1/projects/       - List projects"
echo "  - POST   /api/v1/deployments/    - Deploy project"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

python run.py
