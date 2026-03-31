# Phase 5: Testnet Deployment Guide

## Overview
This guide walks through deploying all 7 Motoko canisters to the IC testnet, testing them comprehensively, and verifying the complete end-to-end flow.

## Prerequisites

1. **dfx SDK** (version 0.20.0+)
   ```bash
   dfx --version
   ```

2. **Motoko compiler** (included with dfx)
   ```bash
   dfx build --version
   ```

3. **ICP tokens for cycles** (testnet faucet)
   - Request testnet cycles: https://faucet.dfinity.org/

4. **Node.js 18+** and npm
   ```bash
   node --version
   npm --version
   ```

## Step 1: Build All Canisters

### 1.1 Build Motoko Canisters
```bash
cd /home/prasanga/dev/InternetComputer

# Build all canisters
dfx build

# Expected output:
# Building canisters...
# Building canister api_gateway...
# Building canister user_registry...
# Building canister project_manager...
# Building canister deploy_engine...
# Building canister billing...
# Building canister domain_manager...
# Building canister metrics_collector...
# Generating type bindings...
```

### 1.2 Verify Build Artifacts
```bash
# Check canister WASM files
ls -lah .dfx/local/canisters/*/

# Should show 7 .wasm files and declarations
```

## Step 2: Deploy to Testnet

### 2.1 Set Up Testnet Identity
```bash
# Create a new identity for testnet (or use existing)
dfx identity new testnet-identity
dfx identity use testnet-identity

# Get your principal
dfx identity get-principal
# Output: your-principal-id

# Export wallet canister ID (needed for cycles)
dfx identity get-wallet --ic
```

### 2.2 Request Testnet Cycles
```bash
# Go to https://faucet.dfinity.org/
# Paste your principal ID
# Get 500T cycles (enough for deployment and testing)

# Verify cycles received
dfx wallet balance --ic
# Output: 500_000_000_000_000 cycles
```

### 2.3 Deploy Canisters to IC
```bash
# Deploy all canisters to mainnet (testnet is same as IC)
dfx deploy --ic

# Or deploy specific canisters in order:
dfx deploy --ic api_gateway
dfx deploy --ic user_registry
dfx deploy --ic project_manager
dfx deploy --ic deploy_engine
dfx deploy --ic billing
dfx deploy --ic domain_manager
dfx deploy --ic metrics_collector

# This will output canister IDs:
# api_gateway: xxx-xxx-xxx-cai
# user_registry: xxx-xxx-xxx-cai
# ... (6 more)
```

### 2.4 Verify Deployments
```bash
# Check canister status
dfx canister status api_gateway --ic
dfx canister status user_registry --ic
# ... (repeat for all 7)

# Expected output:
# Canister status call succeeded.
# Status: running
# ...
```

## Step 3: Update Canister IDs

### 3.1 Update Configuration
```bash
# Copy canister IDs from deployment
# Update src/api_gateway/main.mo with inter-canister calls
# Update frontend environment if needed

# Store IDs in canister_ids.json
cat > canister_ids.json <<EOF
{
  "api_gateway": "your-canister-id-1",
  "user_registry": "your-canister-id-2",
  "project_manager": "your-canister-id-3",
  "deploy_engine": "your-canister-id-4",
  "billing": "your-canister-id-5",
  "domain_manager": "your-canister-id-6",
  "metrics_collector": "your-canister-id-7"
}
EOF
```

## Step 4: Run Test Suite

### 4.1 Update Test Configuration
```bash
# Edit testing/test_motoko_canisters.py
# Set testnet canister IDs

# Or set environment variables:
export CANISTER_API_GATEWAY=xxx-xxx-xxx-cai
export CANISTER_USER_REGISTRY=xxx-xxx-xxx-cai
# ... (repeat for all 7)
```

### 4.2 Run Tests
```bash
cd /home/prasanga/dev/InternetComputer

# Install test dependencies
pip install pytest pytest-asyncio aiohttp

# Run test suite
python testing/test_motoko_canisters.py

# Expected output:
# 📋 Testing User Registry Canister
# ✅ Signup with valid credentials (25.3ms)
# ✅ Email validation (15.2ms)
# ... (all tests)
# 
# TEST SUMMARY
# Total: 65 | Passed: 65 | Failed: 0 | Errors: 0
# Success Rate: 100.0%
```

## Step 5: Test Inter-Canister Communication

### 5.1 User Flow Test
```bash
# Create test user via API Gateway
curl -X POST "https://your-canister-id.ic0.app/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123",
    "displayName": "Test User"
  }'

# Expected response:
# {
#   "accessToken": "...",
#   "refreshToken": "...",
#   "expiresAt": 1234567890,
#   "userId": 1
# }
```

### 5.2 Project Creation Test
```bash
# Create project using returned access token
curl -X POST "https://your-canister-id.ic0.app/api/v1/projects" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-project",
    "description": "Test project",
    "mainFile": "index.html"
  }'

# Expected response:
# {
#   "id": 1,
#   "name": "my-first-project",
#   "status": "pending",
#   "url": "https://xxxxx-1.ic0.app",
#   "canisterId": null
# }
```

### 5.3 Wallet Funding Test
```bash
# Fund wallet via Billing canister
curl -X POST "https://your-canister-id.ic0.app/api/v1/wallet/fund" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "promoCode": "TESTNET-50B"
  }'

# Expected response:
# {
#   "cycleBalance": 50000000000,
#   "usdBalance": 50.0
# }
```

### 5.4 Deployment Test
```bash
# Deploy project
curl -X POST "https://your-canister-id.ic0.app/api/v1/deployments" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": 1,
    "sourceCode": "console.log(\"Hello ICP\");",
    "version": "0.1.0"
  }'

# Expected response:
# {
#   "deploymentId": "deployment-1",
#   "status": "building"
# }

# Check deployment status
curl "https://your-canister-id.ic0.app/api/v1/deployments/deployment-1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Should show progression: queued -> building -> installing -> running
```

## Step 6: Verify Functionality

### 6.1 User Registry Tests
- ✅ Signup with email/password
- ✅ Email verification
- ✅ Login
- ✅ Token refresh
- ✅ Profile retrieval and update

### 6.2 Project Manager Tests
- ✅ Create projects
- ✅ List user projects
- ✅ Get project details
- ✅ Update projects
- ✅ Delete projects
- ✅ Authorization checks

### 6.3 Deploy Engine Tests
- ✅ Deploy projects
- ✅ Track deployment status
- ✅ Get canister info
- ✅ Start/stop canisters
- ✅ View deployment history

### 6.4 Billing Tests
- ✅ Initialize wallets
- ✅ Track balances
- ✅ Fund from promo codes
- ✅ Allocate cycles to canisters
- ✅ View transaction history

### 6.5 Domain Manager Tests
- ✅ Setup custom domains
- ✅ Verify domain ownership
- ✅ Get DNS records
- ✅ Update domain URLs

### 6.6 Metrics Collector Tests
- ✅ Record requests
- ✅ Track metrics
- ✅ Log activities
- ✅ Dashboard aggregation

## Step 7: Load Testing

### 7.1 Install Load Testing Tool
```bash
pip install locust
```

### 7.2 Create Load Test Scenario
```bash
cat > testing/locustfile.py <<EOF
from locust import HttpUser, task, between

class ICPHostingUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def signup(self):
        self.client.post("/api/v1/auth/signup", json={
            "email": "user@test.com",
            "password": "Test123!"
        })
    
    @task
    def get_projects(self):
        self.client.get("/api/v1/projects")
    
    @task
    def get_metrics(self):
        self.client.get("/api/v1/metrics/dashboard")
EOF
```

### 7.3 Run Load Tests
```bash
locust -f testing/locustfile.py \
  --host="https://your-canister-id.ic0.app" \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m

# Monitor performance metrics
# Target: <200ms response time, >95% success rate
```

## Step 8: Security Testing

### 8.1 Authorization Tests
```bash
# Attempt unauthorized access (should fail)
curl "https://your-canister-id.ic0.app/api/v1/projects" \
  -H "Authorization: Bearer invalid-token"
# Expected: 401 Unauthorized

# Try accessing other user's project (should fail)
# (requires creating multiple users)
```

### 8.2 Input Validation Tests
```bash
# Invalid email format
curl -X POST "https://your-canister-id.ic0.app/api/v1/auth/signup" \
  -d '{
    "email": "not-an-email",
    "password": "test"
  }'
# Expected: 400 Bad Request

# Weak password
curl -X POST "https://your-canister-id.ic0.app/api/v1/auth/signup" \
  -d '{
    "email": "test@example.com",
    "password": "weak"
  }'
# Expected: 400 Bad Request (password too short)
```

### 8.3 Rate Limiting Tests
```bash
# Send many requests quickly
for i in {1..10001}; do
  curl "https://your-canister-id.ic0.app/api/v1/projects" \
    -H "Authorization: Bearer token" &
done
wait

# After 10,000 requests per hour:
# Expected: 429 Too Many Requests
```

## Step 9: Monitor and Debug

### 9.1 View Canister Logs
```bash
# Get canister IDs
dfx canister id api_gateway --ic

# View recent activity
# (Note: IC doesn't expose logs like local networks do,
#  monitor via metrics instead)
```

### 9.2 Check Canister Status
```bash
# Get detailed status
dfx canister info api_gateway --ic

# Monitor cycles usage
dfx canister status api_gateway --ic
# Look for: "cycles: X"
```

### 9.3 Test Metrics Collection
```bash
curl "https://your-canister-id.ic0.app/api/v1/metrics/dashboard" \
  -H "Authorization: Bearer token"

# Should show:
# - Total projects
# - Active projects  
# - Total requests
# - Error rates
# - Cycle burn rates
# - Average uptime
```

## Step 10: Prepare for Mainnet

### 10.1 Create Mainnet Identity
```bash
dfx identity new mainnet-prod
dfx identity use mainnet-prod

# Get principal
dfx identity get-principal

# Get wallet for cycles
dfx identity get-wallet
```

### 10.2 Request Production Cycles
```bash
# Buy ICP and convert to cycles
# Or get sponsorship for initial deployment

# Expected cycle requirements per canister:
# - user_registry: ~100M cycles to deploy
# - project_manager: ~100M cycles
# - deploy_engine: ~150M cycles (more complex)
# - billing: ~100M cycles
# - domain_manager: ~80M cycles
# - metrics_collector: ~80M cycles
# - api_gateway: ~150M cycles (orchestrator)
# 
# Total initial: ~900M cycles (~$0.90)
# Ongoing (per 30 days): Variable based on usage
```

### 10.3 Mainnet Deployment
```bash
# Deploy to mainnet (same network ID as testnet "ic")
dfx deploy --ic --identity mainnet-prod

# Note: This is irreversible on mainnet
# Double-check all canister IDs before deploying
```

## Troubleshooting

### Issue: Canisters won't build
```bash
# Clear cache and rebuild
rm -rf .dfx/
dfx build

# Check Motoko syntax
# Look for compilation errors in src/ files
```

### Issue: Deployment fails with insufficient cycles
```bash
# Check cycle balance
dfx wallet balance --ic

# Request more cycles from faucet
# Or convert ICP to cycles
```

### Issue: Inter-canister calls failing
```bash
# Ensure all canister IDs are correct in dependencies
# Check .dfx/ic/canisters/canister_ids.json

# Verify canister exists
dfx canister id user_registry --ic
```

### Issue: High latency/timeouts
```bash
# Check IC network status
# Increase timeout in curl calls
curl --max-time 30 ...

# Implement retry logic in client
```

## Performance Benchmarks

Target metrics for Phase 5:
- **Signup**: <500ms
- **Project creation**: <300ms
- **Deployment initiation**: <1s
- **Metrics retrieval**: <200ms
- **Success rate**: >99.9%
- **Availability**: >99.5% uptime

## Next Steps

1. **Mainnet Preparation**: Get mainnet cycles
2. **Frontend Deployment**: Deploy Next.js app to Vercel or similar
3. **DNS Configuration**: Set up custom domain
4. **Security Audit**: Professional code review
5. **Mainnet Launch**: Deploy Phase 5 to mainnet
