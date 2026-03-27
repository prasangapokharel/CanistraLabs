#!/bin/bash
# API Endpoint Test Runner
# 
# This script runs comprehensive tests against the ICP Hosting Platform API
# Usage: ./run_tests.sh [base_url] [email] [password]

set -e

# Default values from environment variables with fallbacks
BASE_URL="${1:-${API_BASE_URL:-http://localhost:8000}}"
EMAIL="${2:-${TEST_EMAIL:-prasangaramanpokharel@gmail.com}}"
PASSWORD="${3:-${TEST_PASSWORD:-SecurePassword123!}}"

echo "🧪 ICP Hosting Platform - API Endpoint Tests"
echo "============================================"
echo "Base URL: $BASE_URL"
echo "Email: $EMAIL"
echo "Password: [HIDDEN]"
echo ""

# Check if base URL is accessible
if ! curl -s --connect-timeout 5 "$BASE_URL/health" > /dev/null 2>&1; then
    echo "⚠️  Warning: API server at $BASE_URL may not be running"
    echo "   Make sure the backend server is started before running tests"
    echo ""
fi

# Install dependencies if needed
if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Export environment variables for the test script
export API_BASE_URL="$BASE_URL"
export TEST_EMAIL="$EMAIL"  
export TEST_PASSWORD="$PASSWORD"

# Run the comprehensive test suite
echo "🚀 Running comprehensive API tests..."
python3 test_api_endpoints.py \
    --base-url "$BASE_URL" \
    --email "$EMAIL" \
    --password "$PASSWORD" \
    --output "test_results_$(date +%Y%m%d_%H%M%S).json"

echo ""
echo "✅ Test suite completed!"
echo "📄 Detailed results saved to test_results_*.json"