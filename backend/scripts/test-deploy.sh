#!/bin/bash
# ICP Hosting Platform - Test & Deploy
# Runs tests and optionally deploys to IC network

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================"
echo "ICP Hosting - Test & Deploy"
echo "================================"
echo ""

# Activate environment
cd "$PROJECT_ROOT"
source .venv/bin/activate

# Run tests
echo "Running tests..."
python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

echo ""
echo "✓ All tests passed!"
echo "✓ Coverage report: htmlcov/index.html"
echo ""

# Check if user wants to deploy
if [ "$1" = "--deploy-ic" ]; then
    if [ -z "$2" ]; then
        echo "Error: Please provide the ICP repo path"
        echo "Usage: ./scripts/test-deploy.sh --deploy-ic /path/to/icp-repo"
        exit 1
    fi
    
    ICP_REPO="$2"
    if [ ! -d "$ICP_REPO" ]; then
        echo "Error: ICP repo not found: $ICP_REPO"
        exit 1
    fi
    
    echo "Deploying to IC network..."
    echo "Note: This requires dfx to be configured with your ICP identity"
    echo ""
    
    export PATH=$PATH:~/.local/bin
    export DFX_WARNING=-mainnet_plaintext_identity
    
    cd "$ICP_REPO"
    
    echo "Deploying portfolio canister..."
    dfx deploy portfolio --network ic --no-wallet
    
    echo ""
    echo "✓ Deployment complete!"
    echo "✓ Your portfolio is now live on the Internet Computer"
else
    echo "To deploy to IC network, run:"
    echo "  ./scripts/test-deploy.sh --deploy-ic /path/to/icp-repo"
fi
