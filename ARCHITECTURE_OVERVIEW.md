# ICP Hosting Platform - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Frontend (React/Next.js)                     │
│                   (Stores JWT tokens in localStorage)                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ HTTP/REST with JWT Bearer Token
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Application (Python)                        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Auth Layer                                                      │  │
│  │  • Validates JWT tokens                                         │  │
│  │  • Extracts user_id from token.sub                             │  │
│  │  • Enforces ownership checks                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  8 API Routers (55 endpoints total)                             │  │
│  │  ├─ auth.py (8)         ├─ wallet.py (12)                      │  │
│  │  ├─ projects.py (5)     ├─ domains.py (8)                      │  │
│  │  ├─ deployments.py (7)  ├─ metrics.py (4)                      │  │
│  │  ├─ canister.py (5)     └─ cron.py (3)                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│  ┌──────────────────────────────┴───────────────────────────────────┐  │
│  │  12 Service Layer                                               │  │
│  │  ├─ AuthService           ├─ DomainManagementService          │  │
│  │  ├─ ProjectService        ├─ DfxCommand (CLI wrapper)         │  │
│  │  ├─ DeploymentService     ├─ RosettaClient                    │  │
│  │  ├─ ICPIdentityManager    ├─ AutoFundingDetector              │  │
│  │  ├─ CanisterFactory       ├─ EmailVerificationService         │  │
│  │  └─ DynamicDeploymentService  ├─ PasswordResetService         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │  PostgreSQL  │  │  Redis       │  │  Rosetta API │
         │  Database    │  │  (Celery)    │  │  (ICP Ledger)│
         └──────────────┘  └──────────────┘  └──────────────┘
                                                      │
                                                      ▼
                                            ┌──────────────────┐
                                            │  ICP Network     │
                                            │ (Local or IC)    │
                                            │                  │
                                            │ • Ledger Canister│
                                            │ • CMC Canister   │
                                            │ • Management API │
                                            │ • Boundary Nodes │
                                            └──────────────────┘
```

## Data Flow: User Registration

```
1. Frontend: POST /auth/signup {email, username, password, name}
                                │
                                ▼
2. FastAPI: Dependency: get_bearer_token (not applicable, new user)
                                │
                                ▼
3. AuthService.create_user()
   ├─ Check email/username uniqueness
   ├─ Hash password (argon2)
   ├─ Create User record
   └─ session.flush() -> user.id assigned
                                │
                                ▼
4. ICPIdentityManager.create_user_identity()
   ├─ Generate identity_name: user_{id}_{random_8_chars}
   ├─ DfxCommand.identityNew(name)
   │  └─ Creates .dfx/identity/{name} directory
   ├─ DfxCommand.identityExport(name)
   │  └─ Exports encrypted private key
   ├─ EncryptionService.encrypt_data(identity_data)
   │  └─ AES-256 encryption
   └─ Update User table:
      ├─ principal_id
      ├─ account_id
      ├─ encrypted_identity_key
      └─ identity_created_at
                                │
                                ▼
5. Generate JWT Tokens
   ├─ Access Token: {sub: user_id, exp: +24h, type: "access"}
   ├─ Refresh Token: {sub: user_id, exp: +7d, type: "refresh"}
   └─ Sign with JWT_SECRET_KEY (HS256)
                                │
                                ▼
6. Return to Frontend
   ├─ {access_token, refresh_token, expires_in: 86400}
   └─ Frontend stores in localStorage
```

## Data Flow: Project Deployment

```
1. Frontend: POST /deployments/projects/{id}/deploy {code_content}
   + Header: Authorization: Bearer {access_token}
                                │
                                ▼
2. FastAPI Auth Layer
   ├─ get_bearer_token() -> extract token from header
   ├─ verify_token(token, "access") -> {sub: "42", type: "access"}
   └─ get_current_user_id() -> 42
                                │
                                ▼
3. Ownership Check
   ├─ ProjectService.get_project_by_id(session, project_id=123, user_id=42)
   ├─ SQL: SELECT * FROM projects WHERE id=123 AND user_id=42
   └─ If NULL -> raise 404 (project doesn't exist or not owned)
                                │
                                ▼
4. Create Deployment Record
   ├─ status: "pending"
   ├─ message: "Starting deployment..."
   └─ session.flush() -> deployment.id assigned
                                │
                                ▼
5. CanisterFactory.create_project_canister()
   ├─ Get user from DB (user_id=42)
   ├─ ICPIdentityManager.get_user_identity_context(user)
   │  ├─ Decrypt encrypted_identity_key
   │  ├─ Restore .dfx/identity files
   │  └─ Switch dfx context to user's identity
   ├─ DfxCommand.canisterCreate(project_name, controller)
   │  ├─ Calls dfx canister create
   │  └─ Returns: {success, canisterId}
   ├─ DfxCommand.canisterDeploy(canister_id, code_content)
   │  ├─ Calls dfx canister install
   │  └─ Returns: {success, url}
   └─ Update Project table:
      ├─ canister_id
      ├─ principal_id
      ├─ url
      └─ deployed_at
                                │
                                ▼
6. Update Deployment Status
   ├─ status: "success"
   ├─ deployment_url: "https://canister.ic0.app"
   ├─ completed_at: datetime.utcnow()
   └─ session.commit()
                                │
                                ▼
7. Return to Frontend
   ├─ {
   │    deployment_id: 1,
   │    canister_id: "abc123...",
   │    url: "https://abc123.ic0.app",
   │    status: "success",
   │    message: "Successfully deployed"
   │  }
   └─ Frontend redirects to deployed URL
```

## Data Flow: Custom Domain Setup

```
1. Frontend: POST /domains/projects/{id}/setup
   {domain_name: "example.com", subdomain: "app"}
                                │
                                ▼
2. Auth & Ownership Check (same as above)
                                │
                                ▼
3. DomainManagementService.setup_custom_domain()
   ├─ Validate project.canister_id exists
   ├─ Check domain not already configured
   ├─ Create CustomDomain record
   │  ├─ domain_name: "example.com"
   │  ├─ subdomain: "app"
   │  ├─ canister_id: project.canister_id
   │  ├─ status: "pending"
   │  └─ session.flush()
   ├─ Generate DNS Config
   │  └─ _generate_dns_config(domain, canister_id)
   │     └─ Returns JSON with CNAME, TXT, ALIAS records
   └─ Create DomainVerification records
      ├─ CNAME: app.example.com -> icp1.io
      ├─ TXT: _canister-id.app.example.com -> {canister_id}
      └─ CNAME: _acme-challenge.app.example.com -> _acme-challenge.icp2.io
                                │
                                ▼
4. Generate ic-domains Content
   └─ _generate_ic_domains_content(domain)
      └─ Returns content for .well-known/ic-domains file
                                │
                                ▼
5. Return Setup Instructions
   ├─ {
   │    domain_id: 5,
   │    domain: "app.example.com",
   │    dns_config: { ... },
   │    ic_domains_content: "...",
   │    next_steps: [
   │      "Configure DNS at registrar",
   │      "Deploy .well-known/ic-domains",
   │      "Verify DNS",
   │      "Register with boundary nodes"
   │    ]
   │  }
   └─ Frontend shows step-by-step guide
                                │
                                ▼
6. User Configures DNS at registrar
   └─ Sets CNAME records as specified
                                │
                                ▼
7. Frontend: POST /domains/{domain_id}/verify-dns
   ├─ DomainManagementService.verify_domain_dns()
   ├─ For each DomainVerification record:
   │  └─ Query DNS for record
   │     └─ Mark verified: true when found
   └─ Update CustomDomain.dns_configured = true
                                │
                                ▼
8. Frontend: POST /domains/{domain_id}/register
   ├─ DomainManagementService.register_with_icp_boundary_nodes()
   ├─ HTTP outcall to https://icp0.io/register-domain
   ├─ Boundary nodes register domain internally
   └─ Update CustomDomain.status = "active"
                                │
                                ▼
9. SSL Certificate Auto-Issued
   ├─ Boundary nodes issue SSL cert via ACME
   └─ Update CustomDomain:
      ├─ ssl_active = true
      ├─ ssl_issued_at = datetime
      └─ ssl_expires_at = datetime(+1 year)
```

## Data Flow: Wallet Balance Check

```
1. Frontend: GET /wallet/identity
   + Header: Authorization: Bearer {access_token}
                                │
                                ▼
2. Auth: Extract user_id from token
                                │
                                ▼
3. ICPIdentityManager.get_user_identity_context()
   ├─ Check cache first (wallet_cache)
   └─ If cached and fresh, return cached
                                │
                                ▼
4. Fetch User from DB
   └─ Get user.principal_id, user.account_id
                                │
                                ▼
5. AutoFundingDetector.check_user_funding_status()
   ├─ Query Rosetta API for ICP balance
   │  └─ GET /account/balance?principal_id={principal_id}
   ├─ Query Management Canister for cycles
   │  └─ call_canister("management_canister", "canister_status")
   └─ Determine funding_required
      └─ funded = (icp_balance > 0) OR (cycles_balance > 20M)
                                │
                                ▼
6. Format Response
   ├─ {
   │    identity_name: "user_42_abc1234",
   │    principal_id: "rrkah-fqaaa-...",
   │    account_id: "0x1234...abcd",
   │    cycles_balance: "50000000000",
   │    icp_balance: "1000000000",  # in e8s (10 ICP)
   │    formatted_icp: "10 ICP",
   │    formatted_cycles: "50.00 BC",  # billion cycles
   │    funding_required: false,
   │    auto_convert_available: true,
   │    status: "active"
   │  }
   └─ Cache result (5 min TTL)
                                │
                                ▼
7. Return to Frontend
   └─ Display wallet info in UI
```

## Database Schema (Simplified)

```sql
-- Core User Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    principal_id VARCHAR(255) UNIQUE,  -- ICP principal
    account_id VARCHAR(255) UNIQUE,    -- ICP account
    encrypted_identity_key TEXT,       -- AES-256 encrypted
    wallet_cycles_balance VARCHAR(50),
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Projects Table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    canister_id VARCHAR(255) UNIQUE,
    principal_id VARCHAR(255),
    url VARCHAR(255) UNIQUE,
    language VARCHAR(50) DEFAULT 'motoko',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deployed_at TIMESTAMP
);

-- Deployments Table
CREATE TABLE deployments (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    message TEXT,
    error_message TEXT,
    error_details TEXT,
    logs TEXT,
    canister_id VARCHAR(255),
    deployment_url VARCHAR(500),
    task_id VARCHAR(255) UNIQUE,  -- Celery task ID
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Custom Domains Table
CREATE TABLE custom_domains (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(255),
    canister_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    dns_configured BOOLEAN DEFAULT FALSE,
    ssl_active BOOLEAN DEFAULT FALSE,
    ssl_issued_at TIMESTAMP,
    ssl_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Project Enrollments (RBAC)
CREATE TABLE project_enrollments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'editor',  -- owner, admin, editor, viewer
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);
```

## Service Dependencies

```
AuthService
├─ Uses: EncryptionService, ICPIdentityManager
└─ Called by: API auth endpoints

ProjectService
├─ Called by: Projects API, Deployments API, Domains API
└─ Pure business logic, no external deps

DeploymentService
├─ Calls: ICPService, DfxCommand
├─ Uses: ProjectService to get project
└─ Called by: Deployments API

ICPIdentityManager
├─ Calls: DfxCommand, EncryptionService
├─ Used by: AuthService, DeploymentService, CanisterFactory
└─ Manages user ICP identities

CanisterFactory
├─ Calls: ICPIdentityManager, DfxCommand, Rosetta API
└─ Called by: Deployments API, Auto-deployment system

DomainManagementService
├─ Calls: DfxCommand, DNS APIs, HTTP outcalls
└─ Called by: Domains API

DfxCommand
├─ Calls: subprocess to run dfx CLI
└─ Used by: All ICP-related services

RosettaClient
├─ Calls: ICP Ledger via Rosetta API
└─ Used by: AutoFundingDetector, Wallet API

AutoFundingDetector
├─ Calls: RosettaClient, Management Canister
└─ Used by: Wallet API, Auto-deployment system
```

## Key Files Structure

```
backend/
├── app/
│   ├── models/           # 8 SQLAlchemy models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── deployment.py
│   │   ├── canister.py
│   │   ├── domain.py
│   │   ├── projectMetrics.py
│   │   ├── enrollment.py
│   │   ├── password_reset_token.py
│   │   └── email_verification_token.py
│   ├── services/         # 12 service classes
│   │   ├── auth.py (83 LOC)
│   │   ├── projects.py (107 LOC)
│   │   ├── deployment.py (215 LOC)
│   │   ├── icpIdentityManager.py (435 LOC)
│   │   ├── canisterFactory.py (350 LOC)
│   │   ├── domainManagement.py (482 LOC)
│   │   ├── dfxCommand.py (523 LOC)
│   │   ├── dynamicDeployment.py (269 LOC)
│   │   ├── autoFundingDetector.py (388 LOC)
│   │   ├── rosettaClient.py (461 LOC)
│   │   ├── email_verification.py (247 LOC)
│   │   └── password_reset.py (201 LOC)
│   ├── api/v1/           # 8 routers
│   │   ├── auth.py (55 endpoints)
│   │   ├── projects.py
│   │   ├── deployments.py
│   │   ├── wallet.py
│   │   ├── domains.py
│   │   ├── metrics.py
│   │   ├── canister.py (cleanDfx.py)
│   │   └── cron.py
│   ├── utils/
│   │   ├── security.py (JWT, password hashing)
│   │   ├── encryption.py (AES-256)
│   │   └── rate_limit.py
│   ├── database/
│   │   ├── db.py (SQLAlchemy setup)
│   │   └── init.py (migrations)
│   ├── config.py         # Settings (Pydantic)
│   └── main.py           # FastAPI app factory
├── migrations/           # Alembic migrations
├── pyproject.toml        # Dependencies
└── README.md
```

---

**Continue reading**: See BACKEND_ANALYSIS.md for detailed component breakdown
