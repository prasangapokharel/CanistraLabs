# Setup Guide

Complete step-by-step instructions for setting up the Internet Computer Hosting Platform.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Setup (Automated)](#quick-setup-automated)
3. [Manual Setup](#manual-setup)
4. [Environment Configuration](#environment-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware
- CPU: 2+ cores recommended
- RAM: 4GB minimum (8GB recommended)
- Storage: 2GB free (dfx downloads ~1GB)

### Software
- **Operating System**: Linux or macOS (tested on Ubuntu 20.04+)
- **Python**: 3.14+ (required for loose version constraints)
- **dfx SDK**: 0.31.0+ (automatically installed)
- **Git**: For cloning the repository
- **PostgreSQL**: Optional (SQLite used for local development)

### Network
- Port 4943: dfx replica (local development)
- Port 8000: Backend API server
- Internet connection for downloading dfx and dependencies

## Quick Setup (Automated)

The fastest way to get started:

```bash
# Navigate to the project directory
cd /home/prasanga/dev/InternetComputer

# Run the automated setup script
bash scripts/setup.sh

# Wait for installation to complete (~2-3 minutes)
# The script will:
# 1. Download and install dfx SDK
# 2. Create Python virtual environment
# 3. Install all dependencies
# 4. Initialize the database
```

Once complete, proceed to [Verification](#verification).

## Manual Setup

If the automated script doesn't work or you need more control:

### Step 1: Install dfx SDK

```bash
# Download dfx 0.31.0 from GitHub releases
mkdir -p ~/.local/bin
cd /tmp

# Download the dfx release
wget https://github.com/dfinity/sdk/releases/download/0.31.0/dfx-0.31.0-x86_64-linux.tar.gz

# Extract to ~/.local/bin
tar -xzf dfx-0.31.0-x86_64-linux.tar.gz -C ~/.local/bin

# Verify installation
~/.local/bin/dfx --version
# Should output: dfx 0.31.0
```

### Step 2: Set Up Python Environment

```bash
# Navigate to project root
cd /home/prasanga/dev/InternetComputer

# Create virtual environment with Python 3.14
python3.14 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Python Dependencies

```bash
# Install from pyproject.toml
pip install -e .

# Or install specific requirements
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
pip install pytest pytest-asyncio pytest-cov httpx
```

### Step 4: Initialize Database

```bash
# If using SQLite (local development)
# Database will be created automatically on first run

# If using PostgreSQL (production)
# Update DATABASE_URL in .env with your PostgreSQL connection string
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/icp_hosting"

# Run migrations (if Alembic is set up)
alembic upgrade head
```

### Step 5: Configure Environment

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///./test.db

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-this-to-something-random-and-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# dfx Configuration
DFX_NETWORK=local
DFX_PORT=4943

# Optional: For production ICP deployments
# DFX_IDENTITY=your-identity-name
# DFX_NETWORK=ic
```

## Environment Configuration

### Key Environment Variables

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DATABASE_URL` | `sqlite:///./test.db` | Database connection string | No (SQLite for dev) |
| `SECRET_KEY` | None | JWT signing key (min 32 chars) | Yes |
| `ALGORITHM` | `HS256` | JWT algorithm | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiration | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token expiration | No |
| `DFX_NETWORK` | `local` | dfx network (local, ic, or custom) | No |
| `DFX_PORT` | `4943` | dfx replica port | No |

### Database Configuration

#### SQLite (Recommended for Local Development)
```bash
DATABASE_URL=sqlite:///./test.db
```
- No additional setup required
- Data stored in `test.db` file
- Good for local testing and development

#### PostgreSQL (Recommended for Production)
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/icp_hosting
```

Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Start PostgreSQL
sudo service postgresql start  # Linux
brew services start postgresql # macOS
```

Create database:
```bash
psql -U postgres
CREATE DATABASE icp_hosting;
CREATE USER icp_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE icp_hosting TO icp_user;
\q
```

### JWT Configuration

Generate a secure secret key:

```bash
# Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -hex 32
```

Update `.env`:
```bash
SECRET_KEY=your-generated-key-here
```

## Verification

### Verify dfx Installation

```bash
~/.local/bin/dfx --version
# Expected: dfx 0.31.0
```

### Verify Python Environment

```bash
source venv/bin/activate
python --version
# Expected: Python 3.14.x

pip list | grep -E "fastapi|sqlalchemy|pytest"
# Should show installed packages
```

### Verify Database Connection

```bash
# SQLite (default)
ls -la test.db  # File should exist after first run

# PostgreSQL
psql -U icp_user -d icp_hosting -c "SELECT 1"
# Should return: 1
```

### Run Test Suite

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Expected output: 60 passed in X.XXs
```

### Start Development Server

```bash
# In one terminal, start dfx replica and backend
bash scripts/dev.sh

# Expected output:
# Starting dfx replica on port 4943...
# Starting backend server on port 8000...
# Backend ready at http://localhost:8000
```

### Test API Endpoints

In another terminal:

```bash
# Test health check
curl http://localhost:8000/docs

# Should open Swagger UI in browser, or return HTML

# Test signup
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "secure_password_123",
    "username": "testuser"
  }'

# Expected: User object with ID
```

## Troubleshooting

### dfx Command Not Found

**Problem**: `dfx: command not found`

**Solution**:
```bash
# Verify installation
ls -la ~/.local/bin/dfx

# Add to PATH (temporary)
export PATH="$HOME/.local/bin:$PATH"

# Or make permanent, add to ~/.bashrc or ~/.zshrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Python Version Mismatch

**Problem**: `Python 3.14 required`

**Solution**:
```bash
# Check installed Python versions
python3 --version
python3.14 --version

# If 3.14 not available, install it
sudo apt-get install python3.14 python3.14-venv  # Ubuntu
brew install python@3.14  # macOS
```

### ModuleNotFoundError: No module named 'fastapi'

**Problem**: Dependencies not installed

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -e .

# Or specific package
pip install fastapi
```

### Port Already in Use

**Problem**: `Address already in use` for port 4943 or 8000

**Solution**:
```bash
# Find and kill process using port
lsof -i :4943  # dfx replica port
lsof -i :8000  # Backend server port

# Kill the process
kill -9 <PID>

# Or use different ports
DFX_PORT=4944 bash scripts/dev.sh
```

### Database Connection Failed

**Problem**: `Cannot connect to database`

**Solution for SQLite**:
```bash
# Delete the database and let it recreate
rm test.db

# Run any pending migrations
alembic upgrade head

# Test again
pytest tests/unit/test_auth.py
```

**Solution for PostgreSQL**:
```bash
# Verify PostgreSQL is running
sudo service postgresql status  # Linux
brew services list | grep postgresql  # macOS

# Check connection string in .env
echo $DATABASE_URL

# Test connection
psql "$DATABASE_URL"

# If connection fails, verify:
# 1. PostgreSQL service is running
# 2. Database exists: psql -l
# 3. User has permissions: psql -U postgres -d icp_hosting
```

### dfx Replica Won't Start

**Problem**: `dfx start` fails

**Solution**:
```bash
# Kill any existing replica
pkill -f "dfx replica"

# Clear dfx state
rm -rf .dfx

# Try starting again
~/.local/bin/dfx start --background
```

### Test Failures

**Problem**: Tests failing with import errors

**Solution**:
```bash
# Verify environment is activated
source venv/bin/activate

# Reinstall in development mode
pip install -e .

# Clear cache
rm -rf .pytest_cache __pycache__

# Run tests again
pytest tests/ -v
```

### Slow Test Execution

**Problem**: Tests take a long time to run

**Solution**:
```bash
# Run only unit tests (faster)
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_auth.py -v

# Disable asyncio debug
export PYTHONDEVMODE=0
pytest tests/ -v
```

## Post-Installation

After successful setup:

1. **Read the documentation**:
   - [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow
   - [API.md](API.md) - API reference
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design

2. **Start developing**:
   ```bash
   bash scripts/dev.sh
   ```

3. **View API docs**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

4. **Run tests frequently**:
   ```bash
   pytest tests/ -v
   ```

5. **Deploy locally first**:
   ```bash
   bash scripts/test-deploy.sh --local
   ```

## Next Steps

- See [DEVELOPMENT.md](DEVELOPMENT.md) for development workflow
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [API.md](API.md) for API endpoint documentation

---

**Setup Complete!** You're ready to start developing. Run `bash scripts/dev.sh` to begin.
