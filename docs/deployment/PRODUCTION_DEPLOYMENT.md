# PERAI - Production Deployment Guide
# Complete Setup for Testnet & Mainnet Deployment

## CURRENT CANISTER IDS (Already Deployed on IC)

```json
{
  "dynamic_test": {
    "ic": "5ijpj-hyaaa-aaaao-bag3q-cai"
  },
  "test_app": {
    "ic": "5bkev-rqaaa-aaaao-bag2a-cai"
  }
}
```

## PHASE 5 CANISTERS (New - Need Deployment)

The following 7 Motoko canisters need to be deployed:

1. **api_gateway** - Main entry point (orchestrator)
2. **user_registry** - Authentication & user management
3. **project_manager** - Project CRUD operations
4. **deploy_engine** - Deployment orchestration
5. **billing** - Wallet & cycles management
6. **domain_manager** - Custom domains & DNS
7. **metrics_collector** - Analytics & monitoring

---

## STEP 1: PREPARATION

### 1.1 Verify Environment

```bash
cd /home/prasanga/dev/InternetComputer

# Check all required files exist
ls -la .env.local .env.testnet .env.mainnet dfx.json
echo "✅ Environment files ready"

# Check dfx installation
dfx --version
# Expected: dfx 0.20.0 or higher

# Check Motoko source
ls -la src/*/main.mo
echo "✅ All 7 Motoko canisters present"
```

### 1.2 Configure Your Identity

```bash
# Use existing identity or create new
dfx identity list

# Set default identity for IC
dfx identity use default

# Or create new mainnet identity
dfx identity new mainnet-prod
dfx identity use mainnet-prod

# Get your principal
dfx identity get-principal
# Output: xxxxx-xxxxx-xxxxx-xxxxx-xxxxx

# Save this - needed for wallet configuration
```

---

## STEP 2: CYCLES REQUIREMENTS & COSTS

### 2.1 Cycle Requirements per Canister

| Canister | Deploy Cost | Estimated Monthly | Total Year 1 |
|----------|------------|------------------|------------|
| api_gateway | 150M | $10-20 | $120-240 |
| user_registry | 100M | $5-10 | $60-120 |
| project_manager | 100M | $5-10 | $60-120 |
| deploy_engine | 150M | $10-20 | $120-240 |
| billing | 100M | $5-10 | $60-120 |
| domain_manager | 80M | $3-5 | $36-60 |
| metrics_collector | 80M | $3-5 | $36-60 |
| **TOTAL INITIAL** | **760M cycles** | **$41-80/mo** | **$492-960/yr** |

**1 billion cycles ≈ $1 USD**

### 2.2 Calculate Your Cycle Needs

```bash
# Conversion rates:
# 1 ICP = 1 trillion cycles (1,000B cycles)
# 1 trillion cycles ≈ $1,000 USD
# So: 1 ICP ≈ $1,000 value in cycles

# For initial deployment + 3 months operation:
# Initial: 760M cycles = 0.00076 ICP
# 3 months operation: ~150-240B cycles = 0.15-0.24 ICP
# TOTAL NEEDED: ~0.25 ICP (~$250 USD)

# For 1 year operations:
# Initial + 12 months: ~1-1.5 ICP (~$1,000-1,500 USD)
```

### 2.3 Check Your Cycle Balance

```bash
# Check current cycles balance
dfx wallet balance --ic

# Example output:
# 3_000_000_000_000 cycles (3,000B or 3 ICP equivalent)

# If insufficient, request more from faucet or buy ICP
```

---

## STEP 3: TESTNET DEPLOYMENT (Free - Use Testnet Faucet)

### 3.1 Get Testnet Cycles

```bash
# Visit: https://faucet.dfinity.org/

# 1. Enter your principal:
# xxxxx-xxxxx-xxxxx-xxxxx-xxxxx

# 2. Request cycles (500T cycles = 500,000M cycles FREE)
# This is PLENTY for testing all 7 canisters

# 3. Verify receipt
dfx wallet balance --ic
# Should show: 500_000_000_000_000 cycles
```

### 3.2 Build All Canisters

```bash
# Clean build
rm -rf .dfx/local .dfx/ic

# Build
dfx build

# Expected output:
# Building canisters...
# Building canister api_gateway...
# Building canister user_registry...
# ... (7 canisters total)
# Generating type bindings...
# Build successful.
```

### 3.3 Deploy to Testnet (IC)

```bash
# Set environment
source .env.testnet

# Deploy all canisters (--ic = IC testnet)
dfx deploy --ic

# Or deploy individually for debugging:
dfx deploy api_gateway --ic
dfx deploy user_registry --ic
dfx deploy project_manager --ic
dfx deploy deploy_engine --ic
dfx deploy billing --ic
dfx deploy domain_manager --ic
dfx deploy metrics_collector --ic

# SAVE THE CANISTER IDS!
# Output will show:
# Deployed canisters.
# Canister URLs:
#   api_gateway: https://xxxxx-xxxxx-xxxxx.ic0.app
#   user_registry: https://xxxxx-xxxxx-xxxxx.ic0.app
#   ... (6 more)
```

### 3.4 Update .env.testnet with Real Canister IDs

```bash
# Edit .env.testnet
# Replace placeholder canister IDs with real ones from deployment

nano .env.testnet

# Update these lines:
CANISTER_ID_API_GATEWAY=xxxxx-xxxxx-xxxxx-cai  # From deployment
CANISTER_ID_USER_REGISTRY=xxxxx-xxxxx-xxxxx-cai
CANISTER_ID_PROJECT_MANAGER=xxxxx-xxxxx-xxxxx-cai
CANISTER_ID_DEPLOY_ENGINE=xxxxx-xxxxx-xxxxx-cai
CANISTER_ID_BILLING=xxxxx-xxxxx-xxxxx-cai
CANISTER_ID_DOMAIN_MANAGER=xxxxx-xxxxx-xxxxx-cai
CANISTER_ID_METRICS_COLLECTOR=xxxxx-xxxxx-xxxxx-cai
```

### 3.5 Test Testnet Deployment

```bash
# Test health check
curl "https://xxxxx-xxxxx-xxxxx.ic0.app/health"

# Test signup
curl -X POST "https://xxxxx-xxxxx-xxxxx.ic0.app/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123",
    "displayName": "Test User"
  }'

# Test project creation
curl -X POST "https://xxxxx-xxxxx-xxxxx.ic0.app/api/v1/projects" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "testnet-project",
    "description": "Testing on testnet"
  }'

echo "✅ Testnet deployment working!"
```

---

## STEP 4: MAINNET DEPLOYMENT (Requires ICP Payment)

### 4.1 Acquire ICP for Cycles

**Option A: Buy ICP from Exchange**
```
Exchanges: Coinbase, Kraken, Binance, etc.
Amount needed: ~0.25-1 ICP (~$250-1000)
- Initial deployment: 0.76 ICP
- First 3 months: +0.15-0.24 ICP
```

**Option B: Use Existing ICP**
```
If you already have ICP in a wallet:
- NNS dapp: https://nns.ic0.app
- Plug wallet
- NFID
```

**Option C: Mainnet Sponsorship**
```
Contact DFINITY Foundation:
- Enterprise support: https://dfinity.org/apply
- Grant program: https://dfinity.org/grants
```

### 4.2 Convert ICP to Cycles

```bash
# Method 1: Using NNS dapp
# 1. Go to https://nns.ic0.app
# 2. Login with your hardware wallet or plug
# 3. Select your neuron
# 4. "Follow" the governance proposal to convert ICP → Cycles

# Method 2: Direct cycles transfer (simpler)
# 1. Go to https://ic.rocks
# 2. Search your principal
# 3. Use wallet integration to transfer ICP
# 4. Automatically converts to cycles

# Verify cycles received
dfx wallet balance --ic
# Should show your cycles balance
```

### 4.3 Prepare Mainnet Identity

```bash
# Create mainnet-specific identity
dfx identity new mainnet-production
dfx identity use mainnet-production

# Get principal
dfx identity get-principal
# Save this principal ID

# Ensure this identity has cycles
dfx wallet balance --ic
```

### 4.4 Create .env.mainnet with Real Data

```bash
# Copy template
cp .env.mainnet.example .env.mainnet

# Edit with REAL values
nano .env.mainnet

# Critical settings:
# =============================================================================
ENVIRONMENT=production
SECRET_KEY=generate-strong-random-value-here-min-32-chars
JWT_SECRET=generate-strong-random-value-here-min-32-chars

# Database (REAL production DB)
DATABASE_URL=postgresql://user:secure_password@prod-db.example.com:5432/perai_prod

# Email (YOUR SMTP)
SMTP_HOST=smtp.hostinger.com
SMTP_USERNAME=official@sunsari2.com
SMTP_PASSWORD=xXQv&h#Z2
SMTP_FROM_EMAIL=official@sunsari2.com

# ICP (YOUR MAINNET CANISTER IDS - get from testnet first)
CANISTER_ID_API_GATEWAY=xxxxx-xxxxx-xxxxx-cai
CANISTER_ID_USER_REGISTRY=xxxxx-xxxxx-xxxxx-cai
# ... (repeat for all 7)

# Cycles
CYCLES_PER_PROJECT=200000000000  # 200B per project

# Performance
UVICORN_WORKERS=8  # Production scale
```

### 4.5 Deploy to Mainnet

```bash
# Use mainnet identity
dfx identity use mainnet-production

# Clean build
rm -rf .dfx/local

# Build
dfx build

# IMPORTANT: Verify cycle balance before deployment
dfx wallet balance --ic
# Must show: > 900_000_000 (900M cycles minimum)

# Deploy to mainnet (--ic uses mainnet)
dfx deploy --ic

# VERIFY DEPLOYMENT
dfx canister status api_gateway --ic
# Should show: Canister status call succeeded

# Save all canister IDs
dfx canister id api_gateway --ic  # Repeat for all 7
```

### 4.6 Update canister_ids.json

```bash
# Create production record
cat > canister_ids.json <<'EOF'
{
  "mainnet_production": {
    "api_gateway": "xxxxx-xxxxx-xxxxx-cai",
    "user_registry": "xxxxx-xxxxx-xxxxx-cai",
    "project_manager": "xxxxx-xxxxx-xxxxx-cai",
    "deploy_engine": "xxxxx-xxxxx-xxxxx-cai",
    "billing": "xxxxx-xxxxx-xxxxx-cai",
    "domain_manager": "xxxxx-xxxxx-xxxxx-cai",
    "metrics_collector": "xxxxx-xxxxx-xxxxx-cai"
  },
  "testnet": {
    "dynamic_test": "5ijpj-hyaaa-aaaao-bag3q-cai",
    "test_app": "5bkev-rqaaa-aaaao-bag2a-cai"
  }
}
EOF

git add canister_ids.json
git commit -m "mainnet: Update canister IDs after production deployment"
```

---

## STEP 5: POST-DEPLOYMENT VERIFICATION

### 5.1 Health Checks

```bash
# 1. API Gateway Health
curl "https://[canister-id].ic0.app/health"
# Expected: {"status": "healthy"}

# 2. Each canister stats
curl "https://[api-gateway-id].ic0.app/api/v1/stats"

# 3. Database connectivity
# Backend logs should show: "Database connected successfully"

# 4. Email service
# Test email sending to verify SMTP

# 5. Frontend deployment
# Frontend should load and connect to backend
```

### 5.2 Monitor Cycle Consumption

```bash
# Check cycle balance
dfx wallet balance --ic

# Get detailed status
dfx canister status api_gateway --ic
# Shows: cycles: XXXXX

# Monitor all canisters
for canister in api_gateway user_registry project_manager deploy_engine billing domain_manager metrics_collector; do
    dfx canister status $canister --ic
done
```

### 5.3 Set Up Monitoring Alerts

```bash
# Configure low cycle alerts
# When cycles < 100M on any canister, send alert

# Add to cron job:
# */6 * * * * /path/to/check-cycles.sh

# Check cycles script:
cat > check-cycles.sh <<'EOF'
#!/bin/bash
for canister in api_gateway user_registry project_manager deploy_engine billing domain_manager metrics_collector; do
    cycles=$(dfx canister status $canister --ic | grep cycles | awk '{print $2}')
    if [ $cycles -lt 100000000 ]; then
        # Send alert email
        echo "⚠️  $canister has low cycles: $cycles" | mail -s "Perai Alert" admin@example.com
    fi
done
EOF

chmod +x check-cycles.sh
```

---

## STEP 6: INSUFFICIENT CYCLES - PAYMENT INSTRUCTIONS

### If You Run Out of Cycles:

```
❌ ERROR: Insufficient cycles for operation
Current balance: 50M cycles
Required: 100M cycles

💰 TO ADD CYCLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPTION 1: Buy ICP (Recommended)
  1. Go to: https://nns.ic0.app
  2. Buy ICP: 0.25 ICP = $250 USD
  3. Convert to cycles (automatic)
  4. Check balance: dfx wallet balance --ic

OPTION 2: Send ICP to Your Wallet
  Wallet Address: [YOUR_PRINCIPAL_ID]
  Payment Address (if needed): [DFI_ADDRESS]
  Amount: 0.25 ICP

OPTION 3: Use Testnet Faucet (Testing Only)
  1. Go to: https://faucet.dfinity.org
  2. Enter principal: [YOUR_PRINCIPAL_ID]
  3. Get 500T free testnet cycles

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After adding cycles:
  dfx wallet balance --ic
  dfx wallet send [CANISTER_ID] 50000000000  # Send 50B
```

---

## STEP 7: ONGOING MAINTENANCE

### 7.1 Daily Operations

```bash
# Check system health
./scripts/health-check.sh

# Monitor logs
tail -f /var/log/perai/app.log

# Check database
psql -h prod-db.example.com -U postgres -d perai_prod -c "SELECT COUNT(*) FROM users;"

# Monitor cycles
dfx wallet balance --ic
```

### 7.2 Weekly Tasks

```bash
# Backup database
pg_dump -h prod-db.example.com -U postgres perai_prod > backup-$(date +%Y%m%d).sql

# Update dependencies
npm update
pip install --upgrade -r requirements.txt

# Check for security updates
dfx canister list
```

### 7.3 Monthly Tasks

```bash
# Review metrics
curl "https://[api-gateway].ic0.app/api/v1/metrics/dashboard"

# Analyze costs
# Review cycle burn rate
# Plan budget for next month

# Update documentation
# Record any issues or improvements

# Plan capacity expansion if needed
```

---

## QUICK START CHECKLIST

```bash
□ Install dfx (v0.20.0+)
□ Create/set identity
□ Request testnet cycles (faucet.dfinity.org)
□ Build Motoko canisters (dfx build)
□ Deploy to testnet (dfx deploy --ic)
□ Update .env.testnet with real canister IDs
□ Test endpoints
□ Prepare mainnet:
  □ Buy/get ICP
  □ Convert ICP to cycles
  □ Create .env.mainnet with real values
□ Deploy to mainnet (dfx deploy --ic)
□ Update canister_ids.json
□ Set up monitoring
□ Configure backups
□ Deploy frontend
□ Test full system
□ Go live! 🚀
```

---

## TROUBLESHOOTING

### Problem: Insufficient Cycles
```
Solution:
1. dfx wallet balance --ic  (check balance)
2. Buy ICP from exchange
3. Convert to cycles via NNS
4. Retry deployment
```

### Problem: Canister Deploy Fails
```
Solution:
1. Check cycles: dfx wallet balance --ic
2. Check code: dfx build
3. Check dfx version: dfx --version
4. Clear cache: rm -rf .dfx/local
5. Retry: dfx deploy --ic
```

### Problem: Inter-canister Calls Fail
```
Solution:
1. Verify all canister IDs are correct
2. Ensure both canisters are running
3. Check firewall/network
4. Add canister to whitelist if needed
```

### Problem: High Cycle Burn
```
Solution:
1. Check for infinite loops
2. Optimize query functions
3. Reduce data transfer
4. Cache frequently accessed data
5. Monitor metrics: GET /metrics/dashboard
```

---

## PRODUCTION CHECKLIST

- [ ] All 7 canisters deployed
- [ ] Canister IDs saved and documented
- [ ] .env.mainnet configured with real values
- [ ] Database backups configured
- [ ] Monitoring and alerts set up
- [ ] SMTP email working
- [ ] Frontend deployed and connected
- [ ] SSL/TLS certificates valid
- [ ] Custom domain configured (if applicable)
- [ ] Cycle balance > 500M
- [ ] Daily health checks automated
- [ ] Weekly backups automated
- [ ] Monthly cost review scheduled
- [ ] Security audit completed
- [ ] Incident response plan documented

---

## SUPPORT & RESOURCES

- **ICP Documentation**: https://internetcomputer.org/docs
- **Motoko Guide**: https://internetcomputer.org/docs/current/motoko/main/motoko
- **dfx CLI**: https://internetcomputer.org/docs/current/developer-docs/backend/motoko/at-a-glance
- **IC Faucet**: https://faucet.dfinity.org
- **IC Dashboard**: https://ic.rocks
- **NNS dapp**: https://nns.ic0.app

---

**Last Updated**: April 1, 2026
**Status**: Production Ready ✅
**Phase**: 5 (Full On-Chain Migration)
