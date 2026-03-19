# Development Guide

Complete guide for developing and contributing to the Internet Computer Hosting Platform.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Running the Application](#running-the-application)
5. [Testing](#testing)
6. [Code Quality](#code-quality)
7. [Debugging](#debugging)
8. [Common Tasks](#common-tasks)
9. [Database Migrations](#database-migrations)
10. [Contributing](#contributing)

## Getting Started

### Prerequisites

- Complete the setup from [SETUP.md](SETUP.md)
- Python 3.14+
- dfx SDK 0.31.0+
- Virtual environment activated

### Initial Setup

```bash
# Navigate to project
cd /home/prasanga/dev/InternetComputer

# Activate virtual environment
source venv/bin/activate

# Verify installation
python --version     # Python 3.14.x
~/.local/bin/dfx --version  # dfx 0.31.0

# Run all tests to confirm everything works
pytest tests/ -v
# Expected: 60 passed in X.XXs
```

## Project Structure

### Detailed Directory Layout

```
/home/prasanga/dev/InternetComputer/
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py              # Authentication endpoints
│   │       ├── deployments.py       # Deployment endpoints
│   │       ├── projects.py          # Project CRUD endpoints
│   │       └── __init__.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User model with auth fields
│   │   ├── project.py              # Project model
│   │   ├── canister.py             # Canister model
│   │   ├── deployment.py           # Deployment model
│   │   └── enrollment.py           # Enrollment (not active)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication service (JWT, hashing)
│   │   ├── projects.py             # Project business logic
│   │   └── deployment.py           # Deployment logic & dfx integration
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                 # User request/response schemas
│   │   ├── project.py              # Project request/response schemas
│   │   └── responses.py            # Standard response schemas
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── icp_utils.py            # dfx commands, canister ops
│   │   ├── security.py             # Password hashing, JWT utils
│   │   ├── icp_direct_deploy.py    # (unused)
│   │   └── motoko_template.py      # (unused)
│   │
│   ├── database/
│   │   └── db.py                   # Database configuration
│   │
│   ├── config.py                   # Environment configuration
│   ├── main.py                     # FastAPI application factory
│   └── __init__.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures & configuration
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_auth.py            # 12 auth tests
│   │   ├── test_projects.py        # 16 project tests
│   │   └── test_security.py        # 13 security tests
│   │
│   └── integration/
│       ├── __init__.py
│       └── test_deployment.py      # 19 deployment integration tests
│
├── scripts/
│   ├── setup.sh                    # Initial setup script
│   ├── dev.sh                      # Development server startup
│   └── test-deploy.sh              # Test & deployment runner
│
├── migrations/                     # Alembic database migrations
│
├── pyproject.toml                  # Python dependencies & config
├── run.py                          # Server entry point
├── README.md                       # Project overview
├── SETUP.md                        # Setup instructions
├── API.md                          # API documentation
├── DEPLOYMENT.md                   # Deployment guide
├── DEVELOPMENT.md                  # This file
├── ARCHITECTURE.md                 # Architecture documentation
├── .env                            # Environment variables (gitignored)
└── .gitignore
```

### Key Directories Explained

| Directory | Purpose |
|-----------|---------|
| `app/api/v1/` | FastAPI endpoint handlers |
| `app/models/` | SQLAlchemy ORM models |
| `app/services/` | Business logic & external integrations |
| `app/schemas/` | Pydantic request/response validation |
| `app/utils/` | Helper functions (icp_utils, security, etc.) |
| `tests/unit/` | Unit tests (isolated, fast) |
| `tests/integration/` | Integration tests (with dfx, slower) |
| `scripts/` | Automation scripts for dev/deploy |
| `migrations/` | Database schema changes (Alembic) |

## Development Workflow

### Step 1: Start Development Environment

```bash
# In terminal 1: Start dfx replica and backend server
bash scripts/dev.sh

# Expected output:
# Starting dfx replica...
# dfx started successfully
# Starting backend server on port 8000...
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

### Step 2: Make Code Changes

Edit files in the `app/` directory. The server auto-reloads on file changes.

**Example: Adding a new endpoint**

```python
# File: app/api/v1/example.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.get("/example")
async def get_example(db: AsyncSession = Depends(get_db)):
    return {"message": "Hello from example endpoint"}
```

### Step 3: Run Tests

In another terminal:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run tests matching pattern
pytest tests/ -k "test_login" -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-show
```

### Step 4: Check API Changes

Open http://localhost:8000/docs in your browser to see interactive API documentation.

The documentation updates automatically as you change the code.

### Step 5: Verify Your Changes

```bash
# Test new endpoint with curl
curl -X GET "http://localhost:8000/api/v1/example" \
  -H "Content-Type: application/json" | jq

# Check response
# Expected: {"message": "Hello from example endpoint"}
```

## Running the Application

### Start All Services

```bash
bash scripts/dev.sh
```

This starts:
1. dfx replica on port 4943
2. Backend API on port 8000

### Access Points

- **API Server**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **dfx Replica**: http://localhost:4943

### Stop Services

```bash
# Press Ctrl+C in each terminal

# Or manually stop:
pkill -f "uvicorn"
~/.local/bin/dfx stop
```

### Restart Services

```bash
# Stop everything
pkill -f "uvicorn"
~/.local/bin/dfx stop

# Wait a few seconds
sleep 3

# Start again
bash scripts/dev.sh
```

## Testing

### Test Structure

```
tests/
├── unit/                          # Fast, isolated tests
│   ├── test_auth.py              # User signup/login
│   ├── test_projects.py          # Project CRUD
│   └── test_security.py          # Password/JWT utilities
│
└── integration/                   # Full stack tests
    └── test_deployment.py        # dfx integration
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests (fast, ~1 second)
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/unit/test_auth.py::test_signup -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html
# Open: htmlcov/index.html in browser

# Run with verbose output
pytest tests/ -vv

# Run with print statements visible
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf
```

### Test Coverage

Current coverage: **68% overall**

By module:
- `app/utils/security.py`: 100% ✓
- `app/api/v1/auth.py`: 93%
- `app/api/v1/projects.py`: 98%
- `app/models/`: 95%+
- `app/services/`: 87%+

### Writing Tests

#### Unit Test Example

```python
# File: tests/unit/test_example.py
import pytest
from app.models.user import User

@pytest.mark.asyncio
async def test_user_creation(db):
    """Test that users can be created"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw"
    )
    db.add(user)
    await db.commit()
    
    assert user.id is not None
    assert user.email == "test@example.com"

@pytest.mark.asyncio
async def test_user_unique_email(db):
    """Test that email uniqueness is enforced"""
    user1 = User(
        email="test@example.com",
        username="user1",
        hashed_password="hashed_pw"
    )
    db.add(user1)
    await db.commit()
    
    # Attempting to create duplicate email should fail
    user2 = User(
        email="test@example.com",
        username="user2",
        hashed_password="hashed_pw"
    )
    db.add(user2)
    
    with pytest.raises(Exception):
        await db.commit()
```

#### Integration Test Example

```python
# File: tests/integration/test_example.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_deploy_project(client: AsyncClient, auth_token: str, project):
    """Test deploying a project to ICP"""
    response = await client.post(
        "/api/v1/deployments",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "project_id": str(project.id),
            "html_content": "<html><body>Hello</body></html>",
            "network": "local"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "canister_id" in data["data"]
```

## Code Quality

### Code Style

We follow **PEP 8** style guide with line length of 100 characters.

```python
# Good
async def authenticate_user(
    email: str,
    password: str,
    db: AsyncSession
) -> Optional[User]:
    """Authenticate user with email and password."""
    # Implementation here
    pass

# Bad
async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[User]:
    pass  # No docstring
```

### Type Hints

Always use type hints:

```python
# Good
async def get_user(user_id: UUID, db: AsyncSession) -> User:
    pass

# Bad
async def get_user(user_id, db):
    pass
```

### Documentation

Add docstrings to functions and classes:

```python
async def deploy_project(
    project_id: UUID,
    html_content: str,
    network: str = "local"
) -> Deployment:
    """
    Deploy a project to Internet Computer.
    
    Args:
        project_id: The project to deploy
        html_content: HTML content as string
        network: Target network (local or ic)
    
    Returns:
        Deployment object with canister info
    
    Raises:
        ValueError: If project not found
        RuntimeError: If deployment fails
    """
    pass
```

### Before Committing

```bash
# Run full test suite
pytest tests/ -v

# Check coverage
pytest tests/ --cov=app --cov-report=term-show

# All tests should pass and coverage should be high (>65%)
```

## Debugging

### Using Print Statements

```python
# Add debug output
print(f"DEBUG: user_id={user_id}, email={email}")

# Run tests with print visible
pytest tests/unit/test_auth.py -s -v
```

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use newer syntax (Python 3.7+)
breakpoint()

# Run tests to hit breakpoint
pytest tests/unit/test_auth.py::test_signup -s
# Will drop into debugger when hit
```

### Debugging Async Code

```python
import asyncio

# Enable debug logging
asyncio.set_debug(True)

# Run with debug output
PYTHONDEVMODE=1 pytest tests/ -v
```

### Checking Database

```bash
# For SQLite (local)
sqlite3 test.db

# List tables
.tables

# Query data
SELECT * FROM users;
SELECT * FROM projects;

# Exit
.quit
```

### Viewing dfx Logs

```bash
# Get dfx replica logs
~/.local/bin/dfx start --log-level debug

# View canister logs
~/.local/bin/dfx canister logs portfolio --network local

# View all dfx output
~/.local/bin/dfx --verbose deploy portfolio --network local
```

### Monitoring Performance

```python
import time

async def slow_function():
    start = time.time()
    # ... do work ...
    elapsed = time.time() - start
    print(f"Execution time: {elapsed:.2f}s")
```

## Common Tasks

### Add New Endpoint

1. **Create the endpoint handler**:
   ```python
   # File: app/api/v1/example.py
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.get("/example")
   async def get_example():
       return {"message": "Hello"}
   ```

2. **Register in main.py**:
   ```python
   from app.api.v1 import example
   
   app.include_router(
       example.router,
       prefix="/api/v1",
       tags=["example"]
   )
   ```

3. **Add tests**:
   ```python
   @pytest.mark.asyncio
   async def test_get_example(client: AsyncClient):
       response = await client.get("/api/v1/example")
       assert response.status_code == 200
   ```

### Add New Model

1. **Create the model**:
   ```python
   # File: app/models/example.py
   from sqlalchemy import Column, String, DateTime
   from sqlalchemy.dialects.postgresql import UUID
   from datetime import datetime
   
   class Example(Base):
       __tablename__ = "examples"
       
       id = Column(UUID, primary_key=True)
       name = Column(String, nullable=False)
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

2. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "Add example table"
   ```

3. **Run migration**:
   ```bash
   alembic upgrade head
   ```

### Update Dependencies

```bash
# Add new package
pip install new_package

# Update pyproject.toml manually with version

# Reinstall in development mode
pip install -e .

# Test everything still works
pytest tests/ -v
```

### Fix Failing Test

```bash
# Run failing test with verbose output
pytest tests/unit/test_auth.py::test_failing -vv -s

# Check assertion error
# Fix the code or test
# Run again to verify fix
pytest tests/unit/test_auth.py::test_failing -v
```

## Database Migrations

### Create Migration

```bash
# After modifying models, create migration
alembic revision --autogenerate -m "Add new field to users"

# Review generated migration
cat migrations/versions/xxxxx_add_new_field.py
```

### Apply Migration

```bash
# Apply all pending migrations
alembic upgrade head

# Check current version
alembic current

# View migration history
alembic history
```

### Rollback Migration

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade xxx_version_id

# Rollback all
alembic downgrade base
```

## Contributing

### Contribution Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes** and test locally:
   ```bash
   bash scripts/dev.sh
   pytest tests/ -v
   ```

3. **Commit changes**:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

4. **Push branch**:
   ```bash
   git push origin feature/my-feature
   ```

5. **Create pull request** on GitHub

### Code Review Checklist

Before submitting a PR:
- [ ] All 60 tests pass
- [ ] Code coverage maintained (>65%)
- [ ] New code has type hints
- [ ] New code has docstrings
- [ ] Follows PEP 8 style guide
- [ ] No unused imports or variables
- [ ] Integration tests added for new features
- [ ] Documentation updated

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

Examples:
```
feat: Add user profile endpoint

- Added GET /api/v1/users/profile endpoint
- User can view their own profile
- Requires authentication

Closes #123
```

## Environment Variables

### Required for Development

```bash
# Database
DATABASE_URL=sqlite:///./test.db

# JWT
SECRET_KEY=dev_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# dfx
DFX_NETWORK=local
DFX_PORT=4943
```

### Optional

```bash
# Logging
LOG_LEVEL=DEBUG

# CORS (for frontend development)
CORS_ORIGINS=["http://localhost:3000"]

# Environment
ENVIRONMENT=development
```

## Performance Tips

### Optimize Database Queries

```python
# Bad: N+1 queries
for project in await db.query(Project).all():
    print(project.owner.name)  # Extra query per project

# Good: Use eager loading
from sqlalchemy.orm import joinedload
projects = await db.query(Project).options(
    joinedload(Project.owner)
).all()
for project in projects:
    print(project.owner.name)  # No extra queries
```

### Use Async Properly

```python
# Bad: Sequential execution
for item in items:
    result = await long_operation(item)  # Wait each time

# Good: Concurrent execution
import asyncio
results = await asyncio.gather(
    *[long_operation(item) for item in items]
)  # Runs in parallel
```

### Cache Results

```python
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_canister_info(canister_id: str):
    return await fetch_from_dfx(canister_id)
```

---

Happy coding! For questions, see the other documentation files or review existing code.
