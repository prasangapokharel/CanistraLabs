# Deployment Guide

Instructions for deploying the Internet Computer Hosting Platform to production on the Internet Computer mainnet.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Deployment (Testing)](#local-deployment-testing)
4. [Production Deployment (IC Mainnet)](#production-deployment-ic-mainnet)
5. [Deployment Architecture](#deployment-architecture)
6. [Monitoring & Management](#monitoring--management)
7. [Troubleshooting](#troubleshooting)

## Overview

### Deployment Targets

1. **Local Network** (Development/Testing)
   - dfx replica on localhost:4943
   - Portfolio canister: `uxrrr-q7777-77774-qaaaq-cai`
   - Purpose: Test deployments before mainnet

2. **IC Mainnet** (Production)
   - Internet Computer mainnet
   - Portfolio canister: `qjtxq-xaaaa-aaaae-ada4q-cai` (user's canister)
   - Purpose: Live production deployments

### Key Requirements

- **dfx SDK**: v0.31.0+
- **Internet Connection**: For IC mainnet deployments
- **ICP Cycles**: For mainnet deployments (cost: ~0.24 ICP per 1GB asset)
- **dfx Identity**: For mainnet deployments (with private key)

## Prerequisites

### 1. Install and Configure dfx

```bash
# Verify dfx installation
~/.local/bin/dfx --version
# Expected: dfx 0.31.0

# If not installed, run setup
bash scripts/setup.sh
```

### 2. Create dfx Identity (For Mainnet Only)

A dfx identity is required to deploy to IC mainnet.

```bash
# Create a new identity
~/.local/bin/dfx identity new my-icp-identity --disable-encryption

# Set as default
~/.local/bin/dfx identity use my-icp-identity

# Get principal ID (needed for funding)
~/.local/bin/dfx identity get-principal
# Output: xxxxx-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx-cai
```

**⚠️ IMPORTANT**: 
- Keep your identity private key secure: `~/.config/dfx/identities/my-icp-identity/identity.pem`
- Never commit identity files to version control
- Back up your identity in a secure location

### 3. Fund Your Account (For Mainnet)

You need ICP tokens to deploy to mainnet.

```bash
# Get your principal address
PRINCIPAL=$(~/.local/bin/dfx identity get-principal)
echo "Principal: $PRINCIPAL"

# You need to:
# 1. Acquire ICP tokens from an exchange or faucet
# 2. Transfer ICP to your canister's account address
# 3. Check balance

# Check your ICP balance
# (Requires quill or other tooling; see ICP documentation)
```

### 4. Prepare Canister (If Not Exists)

The production canister `qjtxq-xaaaa-aaaae-ada4q-cai` should already exist. If deploying to a new canister:

```bash
# Create a new asset canister on mainnet
# (Requires cycles; contact ICP foundation or use cycle faucet)
```

## Local Deployment (Testing)

### Quick Start

```bash
# 1. Ensure dfx replica is running
bash scripts/dev.sh

# 2. In another terminal, run tests and local deployment
bash scripts/test-deploy.sh --local

# 3. Access the deployed application
# Canister: uxrrr-q7777-77774-qaaaq-cai
# URL: http://127.0.0.1:4943/?canisterId=uxrrr-q7777-77774-qaaaq-cai
```

### Step-by-Step Local Deployment

```bash
# 1. Start dfx replica in background
~/.local/bin/dfx start --background

# 2. Navigate to canister directory
cd /home/prasanga/internet-computer-protocol

# 3. Deploy to local network
~/.local/bin/dfx deploy portfolio --network local

# Expected output:
# Deploying all canisters.
# Creating canisters...
# Installing code for canister portfolio, with canister_id uxrrr-q7777-77774-qaaaq-cai
# Deployed canisters.

# 4. Get local canister ID
LOCAL_CANISTER_ID=$(~/.local/bin/dfx canister id portfolio --network local)
echo "Local Canister: $LOCAL_CANISTER_ID"

# 5. Access application
open "http://127.0.0.1:4943/?canisterId=$LOCAL_CANISTER_ID"
```

### Verify Local Deployment

```bash
# Check canister status
~/.local/bin/dfx canister status portfolio --network local

# Check canister modules
~/.local/bin/dfx canister info portfolio --network local

# View logs
~/.local/bin/dfx canister logs portfolio --network local
```

## Production Deployment (IC Mainnet)

### Pre-Deployment Checklist

- [ ] dfx identity created and funded with ICP
- [ ] Production canister exists (or cycles available to create)
- [ ] HTML content tested locally
- [ ] Backend API running and tested
- [ ] Security review completed

### Deployment Steps

#### Step 1: Set Mainnet Identity

```bash
# Use your mainnet identity
~/.local/bin/dfx identity use my-icp-identity

# Verify active identity
~/.local/bin/dfx identity whoami
# Output: my-icp-identity

# Get principal
~/.local/bin/dfx identity get-principal
```

#### Step 2: Configure Mainnet Network

Ensure `dfx.json` in the canister directory is configured for mainnet:

```json
{
  "networks": {
    "ic": {
      "bind": "127.0.0.1:8080",
      "type": "persistent",
      "providers": [
        "https://mainnet.dfinity.network"
      ]
    }
  }
}
```

#### Step 3: Deploy to Mainnet

```bash
# Navigate to canister directory
cd /home/prasanga/internet-computer-protocol

# Set environment for plaintext identity warning
export DFX_WARNING="-mainnet_plaintext_identity"

# Deploy to IC mainnet
~/.local/bin/dfx deploy portfolio --network ic

# Expected output:
# Deploying all canisters.
# Creating canisters...
# Installing code for canister portfolio, with canister_id qjtxq-xaaaa-aaaae-ada4q-cai
# Deployed canisters.
```

#### Step 4: Verify Production Deployment

```bash
# Get mainnet canister ID
CANISTER_ID=$(~/.local/bin/dfx canister id portfolio --network ic)
echo "Production Canister: $CANISTER_ID"

# Check canister status on mainnet
~/.local/bin/dfx canister status portfolio --network ic

# Access deployed application
# URL: https://<canister_id>.ic0.app
open "https://$CANISTER_ID.ic0.app"
```

### Deployment Automation Script

Create `scripts/deploy-mainnet.sh`:

```bash
#!/bin/bash

set -e

CANISTER_NAME="portfolio"
IDENTITY="my-icp-identity"
CANISTER_DIR="/home/prasanga/internet-computer-protocol"

echo "📦 Deploying $CANISTER_NAME to IC Mainnet..."

# 1. Use mainnet identity
echo "🔐 Using identity: $IDENTITY"
~/.local/bin/dfx identity use $IDENTITY

# 2. Get principal
PRINCIPAL=$(~/.local/bin/dfx identity get-principal)
echo "👤 Principal: $PRINCIPAL"

# 3. Navigate to canister directory
cd $CANISTER_DIR

# 4. Deploy to mainnet
echo "🚀 Deploying to IC Mainnet..."
export DFX_WARNING="-mainnet_plaintext_identity"
~/.local/bin/dfx deploy $CANISTER_NAME --network ic

# 5. Get canister ID
CANISTER_ID=$(~/.local/bin/dfx canister id $CANISTER_NAME --network ic)
echo "✅ Deployment successful!"
echo "📍 Canister ID: $CANISTER_ID"
echo "🌐 Access at: https://$CANISTER_ID.ic0.app"

# 6. Verify deployment
echo "🔍 Verifying deployment..."
~/.local/bin/dfx canister status $CANISTER_NAME --network ic
```

Make it executable:

```bash
chmod +x scripts/deploy-mainnet.sh
```

Run the deployment:

```bash
bash scripts/deploy-mainnet.sh
```

## Deployment Architecture

### Local Network Architecture

```
┌─────────────────────────────────────────────────┐
│           Local Development Environment         │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐        ┌──────────────────┐ │
│  │ dfx Replica  │        │ Backend API      │ │
│  │(localhost:   │        │(localhost:       │ │
│  │ 4943)        │        │ 8000)            │ │
│  └──────────────┘        └──────────────────┘ │
│       │                          │             │
│  ┌────▼─────────────────────────▼──────┐     │
│  │  Portfolio Canister (Asset)          │     │
│  │  ID: uxrrr-q7777-77774-qaaaq-cai    │     │
│  │                                      │     │
│  │  ├─ index.html                       │     │
│  │  ├─ styles.css                       │     │
│  │  └─ script.js                        │     │
│  └──────────────────────────────────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### IC Mainnet Architecture

```
┌──────────────────────────────────────────────────────┐
│          Internet Computer Mainnet                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ Portfolio Canister (Asset)                    │  │
│  │ ID: qjtxq-xaaaa-aaaae-ada4q-cai             │  │
│  │                                              │  │
│  │ ├─ index.html                                │  │
│  │ ├─ styles.css                                │  │
│  │ └─ script.js                                 │  │
│  └──────────────────────────────────────────────┘  │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────────────────────────────────┐  │
│  │ HTTPS Gateway (ic0.app)                       │  │
│  │ URL: https://<canister_id>.ic0.app           │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ Backend API Canister (Optional)              │  │
│  │ For server-side logic                         │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## Monitoring & Management

### Check Deployment Status

```bash
# Local network
~/.local/bin/dfx canister status portfolio --network local

# IC Mainnet
~/.local/bin/dfx canister status portfolio --network ic
```

### View Canister Modules

```bash
# List installed modules
~/.local/bin/dfx canister info portfolio --network ic
```

### View Canister Logs

```bash
# Local network
~/.local/bin/dfx canister logs portfolio --network local

# IC Mainnet (limited availability)
~/.local/bin/dfx canister logs portfolio --network ic
```

### Monitor Cycles (Mainnet)

```bash
# Check canister balance
# Note: Requires additional tooling (e.g., quill, ic-utils)

# Estimate cycles for deployment
# 1GB asset ≈ 0.24 ICP (≈ 2.4 trillion cycles at current rate)
```

### Delete Canister

```bash
# Warning: This cannot be undone!

# Local network (safe - can recreate)
~/.local/bin/dfx canister delete portfolio --network local

# IC Mainnet (permanent - requires new canister ID)
~/.local/bin/dfx canister delete portfolio --network ic
```

## Troubleshooting

### Issue: "Cannot reach IC mainnet"

**Problem**: Deployment fails with network error

**Solution**:
```bash
# Check internet connection
ping mainnet.dfinity.network

# Verify dfx configuration
cat .dfx/local/canister_ids.json

# Try with explicit network
~/.local/bin/dfx deploy portfolio --network ic --verbose
```

### Issue: "Identity not found"

**Problem**: dfx cannot find your identity

**Solution**:
```bash
# List available identities
~/.local/bin/dfx identity list

# Check identity file exists
ls ~/.config/dfx/identities/

# Create new identity if needed
~/.local/bin/dfx identity new my-new-identity
```

### Issue: "Insufficient cycles"

**Problem**: Deployment fails with "out of cycles"

**Solution**:
```bash
# Check current balance
# (Requires quill or other tools)

# Add more ICP to your account
# 1. Acquire ICP tokens from exchange
# 2. Transfer to your principal's account
# 3. Wait for balance to update (~1 min)

# Estimate deployment cost
# Small project (< 1MB): ~0.01 ICP
# Medium project (1-10MB): ~0.1 ICP
# Large project (10-100MB): ~1 ICP
```

### Issue: "Canister is empty"

**Problem**: Deployed canister has no content

**Solution**:
```bash
# Verify HTML files exist
ls -la /home/prasanga/internet-computer-protocol/portfolio/

# Rebuild and redeploy
cd /home/prasanga/internet-computer-protocol
~/.local/bin/dfx build portfolio
~/.local/bin/dfx install portfolio --network ic
```

### Issue: "Cannot delete canister"

**Problem**: Canister deletion fails

**Solution**:
```bash
# Canister can only be deleted if:
# 1. You are the controller
# 2. It has a freeze_threshold of 0
# 3. It has enough cycles to delete itself

# Check canister info
~/.local/bin/dfx canister info portfolio --network ic

# If stuck, may need to use quill for direct IC API calls
```

## Rollback Procedures

### Rollback Deployment

If a deployment goes wrong, you can revert to the previous version:

```bash
# 1. Keep previous versions of HTML files
git checkout HEAD~1 portfolio/index.html

# 2. Rebuild
cd /home/prasanga/internet-computer-protocol
~/.local/bin/dfx build portfolio

# 3. Reinstall
~/.local/bin/dfx install portfolio --network ic

# 4. Verify
open "https://<canister_id>.ic0.app"
```

### Check Deployment History

```bash
# View git history of deployments
git log --oneline portfolio/

# View recent changes
git diff HEAD~1 portfolio/index.html
```

## Best Practices

1. **Always Test Locally First**
   ```bash
   bash scripts/dev.sh
   bash scripts/test-deploy.sh --local
   ```

2. **Use Version Control**
   ```bash
   git commit -m "Deploy portfolio v1.0"
   ```

3. **Monitor Cycles**
   - Set up alerts for low cycles
   - Top up before running out

4. **Regular Backups**
   ```bash
   cp -r /home/prasanga/internet-computer-protocol ~/backups/ic-$(date +%Y%m%d)
   ```

5. **Document Changes**
   - Keep changelog of deployments
   - Document any custom configurations

6. **Automate Deployments**
   - Use CI/CD pipelines for production
   - Automate testing before deployment

## Deployment Checklist

- [ ] Local deployment tested and verified
- [ ] HTML content validated
- [ ] dfx identity created and backed up
- [ ] Mainnet canister ID confirmed
- [ ] Sufficient cycles available
- [ ] Git changes committed
- [ ] Pre-deployment backup created
- [ ] dfx version verified (0.31.0+)
- [ ] Network connectivity confirmed
- [ ] Deployment command ready
- [ ] Post-deployment verification plan

## Support & Resources

- **dfx Documentation**: https://internetcomputer.org/docs/current/
- **IC Developer Forum**: https://forum.dfinity.org
- **ICP Token Info**: https://coinmarketcap.com/currencies/internet-computer/
- **Cycles Pricing**: https://internetcomputer.org/docs/current/developer-docs/gas-cost
- **Canister Management**: https://internetcomputer.org/docs/current/developer-docs/production/managing-canisters

---

**Status**: Ready for Production ✓
