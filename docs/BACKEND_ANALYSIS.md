# ICP Hosting Platform - Backend Analysis & Architecture

## Executive Summary

The ICP Hosting Platform is a comprehensive backend system built with **FastAPI + SQLAlchemy** that manages:
- Multi-tenant user authentication and authorization
- ICP canister deployment orchestration
- Custom domain management and SSL integration
- Wallet/identity management with cycles funding
- Real-time metrics collection and monitoring

**Total API Endpoints**: 55 endpoints across 8 routers
**Service Modules**: 12 core services (3,761 lines total)
**Data Models**: 8 core models with complex relationships
**Authentication**: JWT tokens (access + refresh) with ICP principal IDs

---

## 1. DATA MODEL STRUCTURE & RELATIONSHIPS

### Core Models (8 Total)

```
User (Central Hub)
├── Projects (1:N)
│   ├── Deployments (1:N)
│   ├── Canister (1:1)
│   ├── CustomDomains (1:N)
│   │   └── DomainVerifications (1:N)
│   └── ProjectMetrics (1:1)
├── ProjectEnrollments (1:N) [RBAC]
├── PasswordResetTokens (1:N)
└── EmailVerificationTokens (1:N)
```

### 1.1 User Model
**File**: `/backend/app/models/user.py`
```python
class User(Base):
    __tablename__ = "users"
    
    # Primary Keys & Identification
    id: int (PK)
    email: str (unique, indexed) 
    username: str (unique, indexed)
    
    # Authentication
    password_hash: str (argon2)
    email_verified: bool (default: False)
    is_active: bool (default: True)
    is_superuser: bool (default: False)
    
    # ICP Identity (Encrypted)
    dfx_identity_name: str
    principal_id: str (unique, indexed)
    account_id: str (unique, indexed)
    encrypted_identity_key: str (encrypted)
    wallet_cycles_balance: str (default: "0")
    identity_created_at: datetime
    
    # Timestamps
    created_at: datetime (default: UTC now)
    updated_at: datetime (auto-updated)
    full_name: str (optional)
    
    # Relationships
    projects: list[Project] (1:N, cascade delete)
    enrollments: list[ProjectEnrollment] (1:N)
    custom_domains: list[CustomDomain] (1:N)
    password_reset_tokens: list[PasswordResetToken] (1:N)
    email_verification_tokens: list[EmailVerificationToken] (1:N)
```

**Key Constraints**:
- Email + username unique globally
- Principal ID + Account ID encrypted at rest
- Automatic ICP identity creation on signup

---

### 1.2 Project Model
**File**: `/backend/app/models/project.py`
```python
class ProjectStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    PAUSED = "paused"

class Project(Base):
    __tablename__ = "projects"
    
    # Primary Keys
    id: int (PK)
    user_id: int (FK, indexed)
    
    # Metadata
    name: str
    description: str (optional)
    language: str (default: "motoko")
    code_content: str (optional, stores code)
    
    # Deployment Info
    status: str (ProjectStatus)
    canister_id: str (unique, indexed)
    principal_id: str (indexed)
    url: str (unique, indexed) [Format: https://{hash}-{id}.ic0.app]
    deployed_at: datetime (optional)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    owner: User (N:1)
    canister: Canister (1:1, cascade)
    deployments: list[Deployment] (1:N, cascade)
    enrollments: list[ProjectEnrollment] (1:N, cascade)
    custom_domains: list[CustomDomain] (1:N, cascade)
```

**Key Features**:
- Unique auto-generated URL per project
- Single canister per project
- Tracks deployment history via Deployments table

---

### 1.3 Deployment Model
**File**: `/backend/app/models/deployment.py`
```python
class DeploymentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    QUEUED = "queued"

class Deployment(Base):
    __tablename__ = "deployments"
    
    # Primary Keys
    id: int (PK)
    project_id: int (FK, indexed)
    
    # Status Tracking
    status: str (DeploymentStatus)
    version: int (default: 1)
    message: str (optional)
    error_message: str (optional)
    error_details: str (optional)
    logs: str (optional, deployment logs)
    
    # Task Tracking
    task_id: str (unique, indexed, for Celery)
    retry_count: int (default: 0)
    
    # Deployment Details
    canister_id: str (indexed)
    project_path: str
    deployment_url: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    started_at: datetime (optional)
    completed_at: datetime (optional)
    
    # Relationships
    project: Project (N:1)
```

**Key Features**:
- Tracks retry attempts
- Celery task integration
- Full error logging and details
- Version tracking for rollbacks

---

### 1.4 Canister Model
**File**: `/backend/app/models/canister.py`
```python
class CanisterStatus(Enum):
    PENDING = "pending"
    CREATING = "creating"
    ACTIVE = "active"
    FAILED = "failed"
    DELETED = "deleted"

class Canister(Base):
    __tablename__ = "canisters"
    
    # Primary Keys
    id: int (PK)
    project_id: int (FK, indexed)
    
    # ICP Info
    canister_name: str (unique)
    principal_id: str (unique, indexed)
    
    # Status & Metrics
    status: str (CanisterStatus)
    cycles_balance: str (optional)
    memory_usage: str (optional)
    canister_hash: str (optional)
    error_message: str (optional)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    project: Project (1:1)
```

---

### 1.5 CustomDomain Model
**File**: `/backend/app/models/domain.py`
```python
class DomainStatus(Enum):
    PENDING = "pending"
    DNS_CONFIGURED = "dns_configured"
    REGISTERING = "registering"
    ACTIVE = "active"
    FAILED = "failed"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class CustomDomain(Base):
    __tablename__ = "custom_domains"
    
    # Primary Keys
    id: int (PK)
    project_id: int (FK, indexed)
    user_id: int (FK, indexed)
    
    # Domain Info
    domain_name: str (indexed)
    subdomain: str (optional)
    
    # Status
    status: str (DomainStatus)
    registration_status: str (ICP boundary node status)
    
    # ICP Integration
    canister_id: str
    icp_request_id: str (optional)
    
    # DNS Verification
    dns_configured: bool (default: False)
    cname_verified: bool (default: False)
    txt_record_verified: bool (default: False)
    acme_verified: bool (default: False)
    
    # SSL Certificate
    ssl_active: bool (default: False)
    ssl_issued_at: datetime (optional)
    ssl_expires_at: datetime (optional)
    
    # Configuration
    dns_instructions: str (JSON)
    ic_domains_content: str (for .well-known/ic-domains)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    activated_at: datetime (optional)
    
    # Properties
    @property full_domain() -> str  # e.g., "app.example.com"
    @property canister_url() -> str  # e.g., "https://{canister_id}.icp0.io/"
    @property custom_url() -> str    # e.g., "https://app.example.com/"
    
    # Relationships
    project: Project (N:1)
    owner: User (N:1)
    verifications: list[DomainVerification] (1:N, cascade)

class DomainVerification(Base):
    __tablename__ = "domain_verifications"
    
    # Primary Keys
    id: int (PK)
    domain_id: int (FK)
    
    # Verification Records
    record_type: str (CNAME | TXT | ALIAS)
    record_name: str (DNS record name/host)
    record_value: str (DNS record value/target)
    
    # Status
    verified: bool (default: False)
    last_checked: datetime (optional)
    error_message: str (optional)
    
    # Timestamps
    created_at: datetime
    verified_at: datetime (optional)
```

---

### 1.6 ProjectMetrics Model
**File**: `/backend/app/models/projectMetrics.py`
```python
class ProjectMetrics(Base):
    __tablename__ = "project_metrics"
    
    # Primary Keys
    id: int (PK)
    project_id: int (FK, indexed)
    
    # Storage Metrics
    storage_used_bytes: int (BigInt, default: 0)
    storage_limit_bytes: int (BigInt, default: 2GB)
    
    # Performance
    avg_response_time_ms: float (default: 0.0)
    uptime_percentage: float (default: 100.0)
    
    # Traffic
    requests_today: int (default: 0)
    requests_total: int (BigInt, default: 0)
    bandwidth_used_bytes: int (BigInt, default: 0)
    
    # Cycles
    cycles_balance: int (BigInt, default: 0)
    cycles_burned_today: int (BigInt, default: 0)
    cycles_burned_total: int (BigInt, default: 0)
    
    # Deployment
    build_time_seconds: float (optional)
    deployment_size_bytes: int (BigInt, default: 0)
    last_deployment_at: datetime (optional)
    
    # Health
    is_healthy: bool (default: True)
    last_health_check: datetime (auto-updated)
    error_count_today: int (default: 0)
    
    # SSL & Domains
    ssl_status: str (default: "active")
    custom_domains_count: int (default: 0)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed Properties
    @property storage_used_mb() -> float
    @property storage_limit_mb() -> float
    @property storage_usage_percentage() -> float
    @property deployment_size_mb() -> float
    @property bandwidth_used_mb() -> float
    
    # Relationships
    project: Project (N:1)
```

---

### 1.7 ProjectEnrollment Model (RBAC)
**File**: `/backend/app/models/enrollment.py`
```python
class ProjectRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class ProjectEnrollment(Base):
    __tablename__ = "project_enrollments"
    __table_args__ = (UniqueConstraint("user_id", "project_id"),)
    
    # Primary Keys
    id: int (PK)
    user_id: int (FK, indexed)
    project_id: int (FK, indexed)
    
    # Access Control
    role: str (ProjectRole)
    
    # Timestamps
    created_at: datetime
    
    # Relationships
    user: User (N:1)
    project: Project (N:1)
```

---

### 1.8 Token Models (Auth Verification)
**File**: `/backend/app/models/password_reset_token.py`
```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id: int (PK)
    user_id: int (FK, ondelete=CASCADE, indexed)
    token: str (unique, indexed, 255 chars)
    expires_at: datetime
    is_used: bool (default: False)
    used_at: datetime (optional)
    created_at: datetime
    
    # Methods
    @classmethod create_token_expiry(hours=1) -> datetime
    def is_expired() -> bool
    def is_valid() -> bool  # not used AND not expired
    def mark_as_used() -> None
    
    # Relationships
    user: User (N:1)
```

**File**: `/backend/app/models/email_verification_token.py`
```python
class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    
    id: int (PK)
    user_id: int (FK, ondelete=CASCADE, indexed)
    token: str (unique, indexed)
    expires_at: datetime
    is_used: bool (default: False)
    used_at: datetime (optional)
    created_at: datetime
    
    # Methods (similar to PasswordResetToken)
    @classmethod create_token_expiry(hours=24) -> datetime
    def is_expired() -> bool
    def is_valid() -> bool
    def mark_as_used() -> None
    
    # Relationships
    user: User (N:1)
```

---

## 2. SERVICE LAYER ARCHITECTURE

### 2.1 Service Organization (12 Core Services)

```
Services/
├── auth.py (83 LOC)
│   └── AuthService
├── projects.py (107 LOC)
│   └── ProjectService
├── deployment.py (215 LOC)
│   └── DeploymentService
├── icpIdentityManager.py (435 LOC)
│   └── ICPIdentityManager
├── canisterFactory.py (350 LOC)
│   └── CanisterFactory
├── domainManagement.py (482 LOC)
│   └── DomainManagementService
├── dfxCommand.py (523 LOC)
│   └── DfxCommand
├── dynamicDeployment.py (269 LOC)
│   └── DynamicDeploymentService
├── autoFundingDetector.py (388 LOC)
│   └── AutoFundingDetector
├── rosettaClient.py (461 LOC)
│   └── RosettaClient
├── email_verification.py (247 LOC)
│   └── EmailVerificationService
└── password_reset.py (201 LOC)
    └── PasswordResetService
```

---

### 2.2 AuthService
**Purpose**: User registration, login, verification
**Key Methods**:
```python
class AuthService:
    @staticmethod async create_user(session, user_create) -> User
        # Checks for email/username duplicates
        # Hashes password with argon2
        # Auto-creates ICP identity
        # Returns new User object
    
    @staticmethod async authenticate_user(session, email, password) -> User?
        # Verifies email + password
        # Checks is_active flag
        # Returns User or None
    
    @staticmethod async get_user_by_id(session, user_id) -> User?
    @staticmethod async get_user_by_email(session, email) -> User?
```

---

### 2.3 ProjectService
**Purpose**: CRUD operations for projects
**Key Methods**:
```python
class ProjectService:
    @staticmethod def generate_project_url(user_id, project_id) -> str
        # Returns: https://{8-char-md5-hash}-{project_id}.ic0.app
    
    @staticmethod async create_project(session, user_id, project_create) -> Project
        # Creates new Project with PENDING status
        # Auto-generates URL
    
    @staticmethod async get_user_projects(session, user_id, skip, limit) -> list[Project]
    @staticmethod async get_project_by_id(session, project_id, user_id) -> Project?
    @staticmethod async update_project(session, project, project_update) -> Project
    @staticmethod async delete_project(session, project) -> None (with cascade)
    @staticmethod async get_project_by_canister_id(session, canister_id) -> Project?
    @staticmethod async update_project_status(session, project, status) -> Project
```

---

### 2.4 DeploymentService
**Purpose**: Deploy projects to shared canister
**Configuration**:
```python
SHARED_CANISTER_ID = "uxrrr-q7777-77774-qaaaq-cai"

# Deployment URL Pattern:
# https://uxrrr-q7777-77774-qaaaq-cai.ic0.app/project-{name}/
```

**Key Methods**:
```python
class DeploymentService:
    @staticmethod async deploy_project(session, project, code_content) -> Deployment
        # Creates Deployment record (PENDING)
        # Generates project_path from project.name
        # Calls ICPService.deploy_to_shared_canister()
        # Updates Project status -> DEPLOYED
        # Returns Deployment with success/error status
    
    @staticmethod async get_deployment_status(session, deployment_id) -> Deployment?
    @staticmethod async get_project_deployments(session, project_id, limit, skip) -> list[Deployment]
    @staticmethod async get_canister_status(session, canister_id?) -> dict
        # Hits ICP network or returns cached status
```

---

### 2.5 ICPIdentityManager
**Purpose**: Automatic ICP identity creation and lifecycle
**Key Methods**:
```python
class ICPIdentityManager:
    @staticmethod async create_user_identity(session, user) -> dict
        # Generates unique identity name: user_{user_id}_{random_8_chars}
        # Creates identity via DfxCommand.identityNew()
        # Exports private key
        # Encrypts and stores in User.encrypted_identity_key
        # Returns: {identity_name, principal_id, account_id, funding_required}
    
    @staticmethod async get_user_identity_context(session, user) -> dict
        # Auto-creates if missing
        # Restores identity files from encrypted storage
        # Checks wallet balance
        # Returns: {identity_name, principal_id, cycles_balance, status}
    
    @staticmethod def switch_to_user_identity(user) -> str
        # Switches dfx context to user's identity
    
    @staticmethod async check_wallet_balance(user) -> str
        # Queries ICP network for cycles balance
    
    # Internal helpers:
    @staticmethod def _restore_identity_files(user)
    @staticmethod def _decrypt_identity_data(user) -> dict
```

**Key Constraints**:
- Identity keys encrypted with EncryptionService
- Min funding check: 20,000,000 cycles
- Automatic identity creation on user signup

---

### 2.6 CanisterFactory
**Purpose**: Create individual canisters for projects
**Architecture**:
- Creates one canister PER project (not shared)
- Manages canister lifecycle
- Handles cycles allocation

**Key Methods**:
```python
class CanisterFactory:
    @staticmethod async create_project_canister(
        session, project, html_content, deployment
    ) -> dict
        # Checks funding (minimum required)
        # Creates new canister via dfx
        # Deploys HTML/Motoko code
        # Updates Project with canister_id
        # Returns: {status, canister_id, url, cycles_balance}
    
    # Handles states:
    # 1. pending_funding -> User must fund via ICP transfer
    # 2. creating -> Canister creation in progress
    # 3. deployed -> Ready to serve traffic
```

---

### 2.7 DomainManagementService
**Purpose**: Custom domain setup and lifecycle
**Key Methods**:
```python
class DomainManagementService:
    def __init__(self, network="ic"):
        self.network = network
        self.dfx = DfxCommand(network=network)
        self.icp_boundary_node = "https://icp0.io"
    
    async def setup_custom_domain(
        session, project_id, user_id, domain_name, subdomain?
    ) -> dict
        # Validates project ownership & deployed
        # Creates CustomDomain record (PENDING)
        # Generates DNS config
        # Creates DomainVerification records (CNAME, TXT, ACME)
        # Returns: {dns_config, ic_domains_content, next_steps}
    
    def _generate_dns_config(domain, canister_id) -> dict
        # Returns DNS records needed for setup
    
    def _generate_ic_domains_content(domain) -> str
        # Returns content for .well-known/ic-domains
    
    # Additional methods:
    async verify_domain_dns(session, domain_id) -> dict
    async register_with_icp_boundary_nodes(session, domain_id) -> dict
    async check_domain_registration_status(session, domain_id) -> dict
```

---

### 2.8 DfxCommand
**Purpose**: Low-level ICP CLI wrapper
**Key Methods**:
```python
class DfxCommand:
    def __init__(self, network="ic"):
        self.network = network
    
    # Identity operations
    def identityNew(name) -> {success, principalId, accountId}
    def identityExport(name) -> {success, privateKey}
    def identityGetPrincipal() -> {success, principal}
    def identityList() -> {success, identities}
    
    # Canister operations
    def canisterCreate(name, controller) -> {success, canisterId}
    def canisterDeploy(name, path) -> {success, url}
    def canisterStatus(canister_id) -> {success, status, cycles}
    
    # Wallet operations
    def walletBalance(principal) -> {success, balance}
```

---

### 2.9 AutoFundingDetector
**Purpose**: Check user wallet balance and auto-conversion
**Key Methods**:
```python
class AutoFundingDetector:
    async check_user_funding_status(session, user) -> dict
        # Queries Rosetta API for ICP balance
        # Checks cycles balance
        # Determines if auto-convert available
        # Returns: {
        #     funded: bool,
        #     balance: str (ICP),
        #     cycles_balance: str,
        #     auto_convert_available: bool,
        #     has_pending_icp: bool,
        #     formatted_icp: str,
        #     formatted_cycles: str,
        #     message: str
        # }
    
    def format_cycles(cycles) -> str
        # Converts to TC, BC, MC, or raw count
```

---

### 2.10 RosettaClient
**Purpose**: Integration with ICP Rosetta API
**Key Methods**:
```python
class RosettaClient:
    async get_account_balance(principal_id, account_id) -> dict
        # Queries Rosetta API for balance
    
    async transfer_icp(from_account, to_account, amount) -> dict
        # Submits ICP transfer transaction
    
    async convert_icp_to_cycles(principal_id, icp_amount) -> dict
        # Converts ICP to cycles via CMC
```

---

### 2.11 EmailVerificationService
**Purpose**: Email verification token lifecycle
**Key Methods**:
```python
class EmailVerificationService:
    @staticmethod async create_verification_token(session, user) -> str
        # Creates EmailVerificationToken
        # Sends email with verification link
        # Token expires in 24 hours
        # Returns token string
    
    @staticmethod async verify_email_token(session, token) -> User?
        # Validates token not used/expired
        # Marks user.email_verified = True
        # Marks token as used
        # Returns User or None
```

---

### 2.12 PasswordResetService
**Purpose**: Password reset token lifecycle
**Key Methods**:
```python
class PasswordResetService:
    @staticmethod async create_reset_token(session, email) -> str
        # Finds user by email
        # Creates PasswordResetToken (expires 1 hour)
        # Sends reset email with token
        # Returns token string
    
    @staticmethod async verify_reset_token(session, token) -> User?
        # Validates token not used/expired
        # Returns User or None
    
    @staticmethod async reset_password(session, token, new_password) -> User?
        # Verifies token
        # Hashes new password
        # Marks token as used
        # Returns User or None
```

---

## 3. API ENDPOINTS (55 Total)

### Endpoint Organization by Router

#### 3.1 Authentication (8 endpoints)
```
POST   /api/v1/auth/signup                      ✓ Create user + ICP identity
POST   /api/v1/auth/login                       ✓ Authenticate + JWT tokens
POST   /api/v1/auth/refresh                     ✓ Refresh access token
POST   /api/v1/auth/logout                      ✓ Invalidate token
GET    /api/v1/auth/me                          ✓ Get current user profile
POST   /api/v1/auth/forgot-password             ✓ Initiate password reset
POST   /api/v1/auth/reset-password              ✓ Complete password reset
POST   /api/v1/auth/verify-email                ✓ Verify email token
POST   /api/v1/auth/resend-verification         ✓ Resend verification email
```

#### 3.2 Projects (5 endpoints)
```
POST   /api/v1/projects/                        ✓ Create new project
GET    /api/v1/projects/                        ✓ List user's projects
GET    /api/v1/projects/{project_id}            ✓ Get project details
PUT    /api/v1/projects/{project_id}            ✓ Update project
DELETE /api/v1/projects/{project_id}            ✓ Delete project
```

#### 3.3 Deployments (7 endpoints)
```
POST   /api/v1/deployments/projects/{id}/deploy         ✓ Deploy project
GET    /api/v1/deployments/projects/{id}/deployments    ✓ Get deployment history
GET    /api/v1/deployments/projects/{id}/deployments/{did} ✓ Get deployment status
```

#### 3.4 Wallet Management (12 endpoints)
```
GET    /api/v1/wallet/identity                  ✓ Get ICP identity + balance
POST   /api/v1/wallet/refresh-balance           ✓ Refresh wallet balance
GET    /api/v1/wallet/funding-instructions      ✓ Get funding address
POST   /api/v1/wallet/send-icp                  ✓ Transfer ICP (user to user)
POST   /api/v1/wallet/send-cycles               ✓ Transfer cycles
POST   /api/v1/wallet/convert                   ✓ Convert ICP to cycles
POST   /api/v1/wallet/convert-icp-to-cycles     ✓ Auto-convert ICP
GET    /api/v1/wallet/balances                  ✓ Get all balances
POST   /api/v1/wallet/recreate-identity         ✓ Create new identity
GET    /api/v1/wallet/identities                ✓ List all identities
GET    /api/v1/wallet/network-status            ✓ ICP network health
POST   /api/v1/wallet/auto-deploy-funded-projects  ✓ Deploy when funded
```

#### 3.5 Domain Management (8 endpoints)
```
POST   /api/v1/domains/projects/{id}/setup      ✓ Setup custom domain
POST   /api/v1/domains/{domain_id}/verify-dns   ✓ Verify DNS records
GET    /api/v1/domains/{domain_id}/status       ✓ Get domain status
POST   /api/v1/domains/{domain_id}/register     ✓ Register with ICP
GET    /api/v1/domains/{domain_id}/check-registration ✓ Check registration
DELETE /api/v1/domains/{domain_id}              ✓ Delete domain
GET    /api/v1/domains/user/domains             ✓ List user's domains
GET    /api/v1/domains/projects/{id}/domains    ✓ List project domains
```

#### 3.6 Metrics (4 endpoints)
```
GET    /api/v1/projects/{project_id}/metrics    ✓ Get project metrics
GET    /api/v1/projects/{project_id}/metrics/live ✓ Get live metrics
GET    /api/v1/dashboard/overview               ✓ Dashboard summary
GET    /api/v1/dashboard/activities             ✓ Recent activities
```

#### 3.7 Canister Management (5 endpoints)
```
POST   /api/v1/cleanDfx/create-canister         ✓ Create canister
POST   /api/v1/cleanDfx/projects/{id}/update-canister ✓ Update canister
GET    /api/v1/cleanDfx/canister/{id}/status    ✓ Get canister status
DELETE /api/v1/cleanDfx/projects/{id}/canister  ✓ Delete canister
GET    /api/v1/cleanDfx/dns-instructions/{id}   ✓ Get DNS help
```

#### 3.8 Cron Jobs (3 endpoints)
```
POST   /api/v1/cron/start                       ✓ Start cron scheduler
POST   /api/v1/cron/stop                        ✓ Stop cron scheduler
POST   /api/v1/cron/trigger                     ✓ Trigger cron job
GET    /api/v1/cron/status                      ✓ Get cron status
```

#### 3.9 Dynamic Deployment (3+ endpoints)
```
POST   /api/v1/dynamicDeployment/project/{id}   ✓ Deploy dynamic project
GET    /api/v1/dynamicDeployment/{id}           ✓ Get deployment status
```

#### 3.10 System (2 endpoints)
```
GET    /health                                   ✓ Health check
GET    /api/v1                                   ✓ API info
```

---

## 4. AUTHENTICATION & AUTHORIZATION PATTERNS

### 4.1 JWT Token Architecture
**File**: `/backend/app/utils/security.py`

```python
# Token Payload Structure
class TokenData:
    sub: str                # User ID as string
    exp: datetime          # Expiration time
    iat: datetime          # Issued at
    type: str              # "access" or "refresh"

# Access Token
- Expiration: 24 hours (configurable)
- Algorithm: HS256
- Contains: user_id

# Refresh Token
- Expiration: 7 days
- Algorithm: HS256
- Contains: user_id

# Storage
- Browser: localStorage / sessionStorage
- Transmission: Authorization: Bearer {token}
```

**Token Functions**:
```python
def create_access_token(data: dict, expires_delta?) -> str
def create_refresh_token(data: dict) -> str
def verify_token(token: str, token_type: str) -> TokenData?
```

---

### 4.2 Request Authentication Flow
```python
# 1. Extract Bearer Token
async def get_bearer_token(authorization: str) -> str
    # Header format: "Bearer {token}"
    # Validates format, returns token

# 2. Extract User ID
async def get_current_user_id(token: str) -> int
    # Verifies token
    # Extracts user_id from token.sub
    # Returns int user_id

# 3. Database Verification
async def authenticate_user(email, password) -> User
    # Query: select User where email = ?
    # Verify: argon2.verify(password, user.password_hash)
    # Check: user.is_active == True
    # Return: User or None
```

---

### 4.3 Authorization Patterns
**Role-Based Access Control (RBAC)**:
```python
class ProjectRole(Enum):
    OWNER = "owner"    # Can delete, invite, deploy
    ADMIN = "admin"    # Can manage, deploy
    EDITOR = "editor"  # Can edit code, deploy
    VIEWER = "viewer"  # Read-only access

# Enforcement Example (Projects endpoint)
async def update_project(project_id, user_id):
    project = get_project_by_id(project_id, user_id)
    if not project:
        # Either project doesn't exist OR user doesn't own it
        raise 404 Not Found
```

**Ownership Verification**:
```python
# Pattern across all endpoints:
project = await ProjectService.get_project_by_id(
    session, project_id, user_id
)

if not project:
    raise HTTPException(404, "Project not found")
    # This implicitly checks ownership
```

---

### 4.4 ICP Principal ID Integration
**Purpose**: Map user to ICP identity for on-chain operations

```python
# User.principal_id = "rrkah-fqaaa-aaaaa-aaaaq-cai"
# User.account_id = "1234567890abcdef..."

# Flow:
1. User signs up
2. AuthService.create_user() called
3. ICPIdentityManager.create_user_identity() triggered
4. DfxCommand.identityNew() creates ICP identity
5. Principal ID + Account ID stored encrypted
6. User can now deploy canisters
```

---

## 5. DATABASE RELATIONSHIPS & CONSTRAINTS

### 5.1 Entity-Relationship Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                          User                               │
│  (id, email✓, username✓, principal_id✓, account_id✓)       │
│  password_hash, encrypted_identity_key, wallet_cycles...   │
└────────────┬────────────────────────────────────────────────┘
             │ 1:N (cascade)
             ├─────────────────────────────────────────────────────┐
             │                                                     │
             ▼                                                     ▼
    ┌────────────────────┐                          ┌──────────────────────┐
    │     Project        │                          │ ProjectEnrollment    │
    │ (id, user_id✓, ...)│◄──────1:N (cascade)─────│ (id, user_id, role)  │
    │ status, url✓       │                          └──────────────────────┘
    │ canister_id✓       │
    └────┬──────┬────────┘
         │1:1   │1:N
         │      └────────────────────────────────┬────────────────────┐
         │                                       │                    ▼
         ▼                                       ▼            ┌──────────────────┐
    ┌────────────────┐              ┌────────────────────┐   │ ProjectMetrics   │
    │   Canister     │              │   Deployment       │   │ (id, project_id) │
    │ (id, status)   │              │ (id, project_id)   │   │ storage, cycles  │
    └────────────────┘              │ status, logs       │   └──────────────────┘
                                    └────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │            CustomDomain                                │
    │ (id, project_id, user_id, domain_name, status)         │
    │ canister_id, ssl_active, dns_configured)               │
    └────────────┬───────────────────────────────────────────┘
                 │1:N (cascade)
                 ▼
    ┌────────────────────────────────────────┐
    │       DomainVerification               │
    │ (id, domain_id, record_type, verified) │
    └────────────────────────────────────────┘

    ┌──────────────────────────────────────────┐
    │      PasswordResetToken                  │
    │ (id, user_id✓, token✓, is_used)          │
    │ expires_at, created_at)                  │
    └──────────────────────────────────────────┘

    ┌──────────────────────────────────────────┐
    │    EmailVerificationToken                │
    │ (id, user_id✓, token✓, is_used)          │
    │ expires_at, created_at)                  │
    └──────────────────────────────────────────┘
```

---

### 5.2 Key Constraints Summary

| Constraint Type | Details |
|---|---|
| **Unique** | User.email, User.username, User.principal_id, User.account_id |
| **Unique** | Project.canister_id, Project.url |
| **Unique** | Canister.principal_id, Canister.canister_name |
| **Unique** | Deployment.task_id |
| **Unique** | PasswordResetToken.token, EmailVerificationToken.token |
| **Foreign Keys** | All relationships use CASCADE on delete |
| **Check** | PasswordResetToken.expires_at > created_at |
| **Check** | DeploymentStatus in {pending, running, success, failed, queued} |
| **Check** | ProjectRole in {owner, admin, editor, viewer} |

---

### 5.3 Cascade Behavior
```python
# When User is deleted:
- Projects CASCADE deleted
  - Deployments CASCADE deleted
  - Canister CASCADE deleted
  - ProjectMetrics CASCADE deleted
  - CustomDomain CASCADE deleted
    - DomainVerification CASCADE deleted
  - ProjectEnrollment CASCADE deleted
- ProjectEnrollment CASCADE deleted
- PasswordResetToken CASCADE deleted
- EmailVerificationToken CASCADE deleted
- CustomDomain CASCADE deleted

# When Project is deleted:
- Deployments CASCADE deleted
- Canister CASCADE deleted
- ProjectMetrics CASCADE deleted
- CustomDomain CASCADE deleted
  - DomainVerification CASCADE deleted
- ProjectEnrollment CASCADE deleted
```

---

## 6. CRITICAL BUSINESS LOGIC FOR MOTOKO MIGRATION

### 6.1 User Management (High Priority)
**Currently in Python**: User registration, password hashing, profile management

**Critical Components**:
- [ ] Email verification workflow
- [ ] Password reset with secure tokens
- [ ] User profile storage + metadata
- [ ] ICP identity lifecycle management (ALREADY integrated with canister ops)

**Motoko Approach**:
```motoko
// Core User Canister
actor Users {
  type User = {
    id: Principal;
    email: Text;
    username: Text;
    email_verified: Bool;
    profile: Profile;
    created_at: Int;
  };
  
  // Store user emails as reverse index (since Motoko can't have unique constraints)
  var emailIndex: HashMap.HashMap<Text, Principal> = HashMap.HashMap(0, Text.equal, Text.hash);
}
```

---

### 6.2 Project Management (High Priority)
**Currently in Python**: CRUD operations, ownership verification, status tracking

**Critical Components**:
- [ ] Create/update/delete projects
- [ ] Project ownership verification
- [ ] Deployment status tracking
- [ ] URL generation (deterministic)

**Motoko Approach**:
```motoko
actor Projects {
  type Project = {
    id: Nat;
    owner: Principal;
    name: Text;
    status: ProjectStatus;
    canister_id: ?CanisterId;
    url: Text;
    created_at: Int;
  };
  
  // Ownership check (NO RBAC in main canister)
  private func verifyOwnership(project_id: Nat, caller: Principal): async Bool {
    let project = projects.get(project_id);
    return project?.owner == caller;
  };
}
```

---

### 6.3 Deployment Orchestration (CRITICAL)
**Currently in Python**: Deploy to shared canister, track status, handle errors

**Critical Components**:
- [ ] Canister creation (per project or shared)
- [ ] Code deployment + updates
- [ ] Deployment status tracking
- [ ] Error handling and rollbacks

**Motoko Approach**:
```motoko
actor Deployments {
  type Deployment = {
    id: Nat;
    project_id: Nat;
    status: DeploymentStatus;
    canister_id: ?CanisterId;
    url: ?Text;
    created_at: Int;
    completed_at: ?Int;
  };
  
  public func deployProject(
    project_id: Nat, 
    code: Blob
  ): async {
    status: Text;
    canister_id: ?CanisterId;
  } {
    // Create canister, install code, return status
  };
}
```

---

### 6.4 Custom Domains (Medium Priority)
**Currently in Python**: DNS configuration, verification, SSL management

**Critical Components**:
- [ ] Domain record creation
- [ ] DNS verification status tracking
- [ ] SSL certificate tracking
- [ ] Domain-to-canister mapping

**Motoko Approach**:
```motoko
actor Domains {
  type CustomDomain = {
    id: Nat;
    project_id: Nat;
    domain_name: Text;
    canister_id: CanisterId;
    status: DomainStatus;
    dns_records: [DnsRecord];
    ssl_active: Bool;
    created_at: Int;
  };
  
  public func setupDomain(
    project_id: Nat,
    domain_name: Text
  ): async {
    success: Bool;
    dns_config: [DnsRecord];
  } {
    // Create domain record, generate DNS config
  };
}
```

---

### 6.5 Wallet & Funding (Medium Priority)
**Currently in Python**: Check ICP balance, handle auto-conversion, track funding

**Critical Components**:
- [ ] ICP balance tracking per user
- [ ] Cycles balance per project
- [ ] Funding status determination
- [ ] Auto-deployment when funded

**Motoko Approach**:
```motoko
actor Wallet {
  type WalletStatus = {
    principal: Principal;
    cycles_balance: Nat;
    icp_balance: Nat;
    funding_required: Bool;
  };
  
  public func getWalletStatus(
    principal: Principal
  ): async WalletStatus {
    // Query ledger for ICP balance
    // Query management canister for cycles
  };
}
```

---

### 6.6 Authentication & Authorization (Medium Priority)
**Currently in Python**: JWT tokens, RBAC, ownership checks

**Critical Components**:
- [ ] JWT token validation (move to frontend or edge layer)
- [ ] Ownership verification (already in each canister)
- [ ] Role-based access control (RBAC via ProjectEnrollment)
- [ ] ICP principal verification

**Motoko Approach**:
```motoko
// Each canister verifies caller() = msg.caller
// No JWT in canister (validate on ingress)

actor Authorization {
  type ProjectRole = {
    #owner;
    #admin;
    #editor;
    #viewer;
  };
  
  public func getUserRole(
    project_id: Nat,
    user_principal: Principal
  ): async ?ProjectRole {
    // Lookup in ProjectEnrollment canister
  };
}
```

---

### 6.7 Metrics & Monitoring (Low Priority)
**Currently in Python**: Mock metrics collection

**Critical Components**:
- [ ] Real-time metrics from canisters
- [ ] Storage usage tracking
- [ ] Cycles burned tracking
- [ ] Uptime/health metrics

**Motoko Approach**:
```motoko
actor Metrics {
  type ProjectMetrics = {
    project_id: Nat;
    storage_bytes: Nat;
    cycles_burned: Nat;
    uptime_percent: Float;
    requests_today: Nat;
  };
  
  public func recordMetric(
    project_id: Nat,
    metric: ProjectMetrics
  ): async () {
    // Store time-series data
  };
}
```

---

## 7. RECOMMENDED MOTOKO CANISTER DECOMPOSITION

### 7.1 Canister Architecture (Microservices Model)

```
┌──────────────────────────────────────────────────────────────────┐
│                     API Gateway (Edge)                           │
│  (Validates JWT, routes to canisters, handles rate limiting)     │
└────────┬──────────────────────────────────────────────────────────┘
         │
         ├─────────────────────┬─────────────────┬────────────┬─────────┐
         │                     │                 │            │         │
         ▼                     ▼                 ▼            ▼         ▼
    ┌─────────┐          ┌──────────┐      ┌────────┐  ┌────────┐ ┌──────────┐
    │  Users  │          │ Projects │      │Domains │  │ Wallet │ │Metrics   │
    └─────────┘          └──────────┘      └────────┘  └────────┘ └──────────┘
         │                    │                  │           │          │
    • Signup             • CRUD ops         • Setup         • Balance   • Collect
    • Auth               • Ownership        • Verify        • Transfer  • Store
    • Profile            • Enroll users     • Status        • Convert   • Query
         │                    │                  │           │          │
         └────────────────────┴──────────────────┴───────────┴──────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │   Deployments        │
                    │   (Shared Infra)     │
                    │                      │
                    │ • Create canisters   │
                    │ • Deploy code        │
                    │ • Track status       │
                    │ • Manage lifecycle   │
                    └──────────────────────┘
```

---

### 7.2 Canister Specifications

#### 7.2.1 Users Canister
**Purpose**: User registration, profile, authentication state
**State**: ~100KB per 1000 users
**Key Operations**:
- `register(email, username, password_hash, principal)`
- `getUserProfile(principal) -> User`
- `updateProfile(principal, profile) -> Bool`
- `verifyEmail(token) -> Bool`
- `getEmailByUsername(username) -> ?Email` (reverse index)

**Upgrade Strategy**: Stable data structure with version migration

---

#### 7.2.2 Projects Canister
**Purpose**: Project CRUD, ownership, enrollment
**State**: ~1MB per 10,000 projects
**Key Operations**:
- `createProject(owner, name, language) -> Project`
- `updateProject(project_id, owner, update) -> Bool`
- `deleteProject(project_id, owner) -> Bool`
- `getUserProjects(owner) -> [Project]`
- `enrollUser(project_id, owner, user, role) -> Bool`
- `checkEnrollment(project_id, user) -> ?ProjectRole`
- `canisterIdToProjectId(canister_id) -> ?Nat` (reverse index)

**Relationships**:
- Calls: Deployments canister (to trigger deploy)
- Calls: Authorization canister (for role verification)

---

#### 7.2.3 Deployments Canister
**Purpose**: Canister creation, code deployment, lifecycle
**State**: ~500KB per 1000 projects
**Key Operations**:
- `createDeployment(project_id, owner) -> Deployment`
- `deployCode(project_id, code: Blob) -> DeploymentResult`
- `getDeploymentStatus(deployment_id) -> DeploymentStatus`
- `getProjectDeployments(project_id) -> [Deployment]`
- `updateDeploymentStatus(deployment_id, status) -> Bool`

**Critical**:
- Actual canister creation via Management canister
- Code installation via Management canister
- Async cycle availability checking

---

#### 7.2.4 Domains Canister
**Purpose**: Custom domain config, DNS verification, SSL tracking
**State**: ~200KB per 1000 domains
**Key Operations**:
- `setupDomain(project_id, domain_name, subdomain?) -> DomainSetup`
- `getDomainStatus(domain_id) -> DomainStatus`
- `verifyDNSRecord(domain_id, record_type) -> Bool`
- `registerWithBoundaryNode(domain_id) -> Bool`
- `getProjectDomains(project_id) -> [Domain]`
- `updateSSLStatus(domain_id, ssl_active) -> Bool`

**External Calls**:
- DNS resolution (off-chain service)
- ICP boundary node registration (HTTP outcalls)

---

#### 7.2.5 Wallet Canister
**Purpose**: Balance tracking, conversion logic, transfer records
**State**: ~50KB per 1000 users
**Key Operations**:
- `getWalletStatus(principal) -> WalletStatus`
- `recordICPTransfer(from, to, amount) -> TransferId`
- `recordCyclesTransfer(from, to, amount) -> TransferId`
- `convertICPToCycles(principal, icp_amount) -> Bool`
- `updateCyclesBalance(principal, delta) -> Nat`
- `checkFundingRequired(principal) -> Bool`

**Integration**:
- Rosetta API for ICP ledger queries
- CMC canister for cycle conversion
- IC Management canister for cycles info

---

#### 7.2.6 Metrics Canister
**Purpose**: Time-series metrics collection and retrieval
**State**: ~1MB+ (can grow large)
**Key Operations**:
- `recordMetric(project_id, metric: Metric) -> ()`
- `getMetricsRange(project_id, start_time, end_time) -> [Metric]`
- `getLatestMetric(project_id) -> Metric`
- `aggregateMetrics(project_id, interval) -> AggregatedMetric`

**Strategy**: Use circular buffer or Ring Buffer for bounded storage

---

#### 7.2.7 Authorization Canister (Optional)
**Purpose**: Centralized RBAC verification
**State**: ~100KB per 10,000 enrollments
**Key Operations**:
- `checkAccess(project_id, user, action) -> Bool`
- `hasRole(project_id, user) -> ?Role`
- `grantRole(project_id, user, role, granter) -> Bool`
- `revokeRole(project_id, user, revoker) -> Bool`

**Note**: Could be embedded in Projects canister if simpler

---

### 7.3 Inter-Canister Communication Pattern

```motoko
// Pattern for canister-to-canister calls

// Users canister checking project ownership via Projects
let projectsCanister = actor("projectscanister_id") : ProjectsInterface;
let project = await projectsCanister.getProject(project_id);
if (project?.owner != caller) { return #err("Unauthorized") };

// With retry logic for resilience
private func callWithRetry<T>(
  f: () -> async T,
  maxRetries: Nat
): async Result<T, Text> {
  for (i in Iter.range(0, maxRetries)) {
    try {
      let result = await f();
      return #ok(result);
    } catch (e) {
      if (i == maxRetries) {
        return #err(Error.message(e));
      };
      // Exponential backoff
      await delay(1 << i);
    };
  };
  #err("Max retries exceeded")
};
```

---

### 7.4 Data Migration Strategy

```
Migration Path:
┌─────────────────────────────────────────────────┐
│  1. Deploy empty Motoko canisters               │
│     (all canisters ready, all cycles reserved)  │
├─────────────────────────────────────────────────┤
│  2. Snapshot Python DB                          │
│     (SELECT * FROM each table)                  │
├─────────────────────────────────────────────────┤
│  3. Transform & Load into Motoko                │
│     (Batch API calls to each canister)          │
├─────────────────────────────────────────────────┤
│  4. Verification Phase                          │
│     (Compare row counts, spot-check hashes)     │
├─────────────────────────────────────────────────┤
│  5. DNS Cutover                                 │
│     (Point frontend to Motoko canisters)        │
├─────────────────────────────────────────────────┤
│  6. Sunset Python Backend                       │
│     (Keep read-only for 30 days, then delete)   │
└─────────────────────────────────────────────────┘

Parallel Running Period: 1-2 weeks
- Writes go to both Python + Motoko (synchronously)
- Reads from Motoko (with Python fallback)
- Ensures data consistency during transition
```

---

### 7.5 Key Design Decisions

| Decision | Rationale |
|---|---|
| **Canister per domain** | Isolation, independent upgrades, clear responsibilities |
| **No shared state** | Reduces deadlocks, improves throughput |
| **Async all the way** | Motoko default, handles inter-canister latency |
| **Stable memory** | Preserve state across upgrades without re-init |
| **Error codes** | Return Result types instead of throwing |
| **No JWT in canister** | Validate at API gateway, use principal inside |
| **Reverse indices** | HashMap for email->principal lookups (no DB unique constraints) |
| **Bounded collections** | Use BTreeMap with size limits to prevent OOM |

---

## 8. AUTHENTICATION & AUTHORIZATION PATTERNS (DETAILED)

### 8.1 Current JWT Flow

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ 1. POST /auth/signup
       │    {email, username, password, name}
       ▼
┌─────────────────────────────┐
│   Auth Service              │
│                             │
│ 1. Check email/username dup │
│ 2. Hash password (argon2)   │
│ 3. Create User object       │
│ 4. Call ICPIdentityManager  │
│ 5. Create ICP identity      │
└──────┬──────────────────────┘
       │
       │ Returns: {user, tokens}
       │
       ▼
┌──────────────────────────────────────┐
│   Generate Tokens                    │
│                                      │
│ Access Token:   {sub: user_id,       │
│                  exp: +24h,          │
│                  iat: now,           │
│                  type: "access"}     │
│                                      │
│ Refresh Token:  {sub: user_id,       │
│                  exp: +7d,           │
│                  iat: now,           │
│                  type: "refresh"}    │
│                                      │
│ Signed with: JWT_SECRET_KEY (HS256)  │
└──────┬───────────────────────────────┘
       │
       │ Returns both tokens
       │
       ▼
┌──────────────────────────┐
│   Store in Browser       │
│                          │
│ localStorage.access_token   │
│ localStorage.refresh_token  │
└──────────────────────────┘
```

---

### 8.2 Request Flow with Token

```
┌──────────────────────────────────────────┐
│   Frontend Makes Authenticated Request   │
│                                          │
│   GET /api/v1/projects/                  │
│   Authorization: Bearer {access_token}   │
└─────────┬────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│   FastAPI Dependency: get_bearer_token  │
│                                         │
│   1. Parse Authorization header         │
│   2. Extract "Bearer {token}"           │
│   3. Return token string                │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│   Dependency: get_current_user_id       │
│                                         │
│   1. Call verify_token(token, "access") │
│   2. Decode JWT (check signature)       │
│   3. Verify type == "access"            │
│   4. Extract user_id from sub           │
│   5. Return int user_id                 │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│   Route Handler                         │
│   (user_id: int)                        │
│                                         │
│   projects = await ProjectService       │
│     .get_user_projects(session, user_id)│
│                                         │
│   Returns only projects where           │
│   project.user_id == user_id            │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│   Response: 200 OK                      │
│   [{project}, {project}, ...]           │
└─────────────────────────────────────────┘
```

---

### 8.3 Token Refresh Flow

```
Frontend detects token expiration (e.g., 401 response)
                    │
                    ▼
         POST /api/v1/auth/refresh
         {refresh_token: "..."}
                    │
                    ▼
      FastAPI: verify_token(refresh_token, "refresh")
      - Check signature valid
      - Check type == "refresh"
      - Extract user_id from sub
                    │
                    ▼
      AuthService.get_user_by_id(user_id)
      - Verify user still exists
      - Verify user.is_active == True
                    │
                    ▼
      Generate NEW access token
      Generate NEW refresh token (optional)
                    │
                    ▼
      Return {access_token, refresh_token, expires_in: 86400}
                    │
                    ▼
      Frontend updates localStorage
      Retries original request with new token
```

---

### 8.4 ICP Principal ID Integration

```
┌────────────────────────────────────────────┐
│  User Signup + ICP Identity Creation       │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  AuthService.create_user()                 │
│  1. Hash password                          │
│  2. Create User record (id=NULL initially) │
│  3. session.flush() <- Auto-increment      │
│  4. Call ICPIdentityManager.create_user_id │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  ICPIdentityManager.create_user_identity() │
│                                            │
│  1. Generate identity_name:                │
│     user_{user_id}_{random_8_chars}        │
│                                            │
│  2. Call DfxCommand.identityNew(name)      │
│     (Creates .dfx/identity/name directory) │
│     Returns: {principalId, accountId}      │
│                                            │
│  3. Call DfxCommand.identityExport(name)   │
│     (Exports private key)                  │
│                                            │
│  4. Encrypt identity data:                 │
│     {                                      │
│       identity_name,                       │
│       principal_id,                        │
│       account_id,                          │
│       private_key,                         │
│       created_at                           │
│     }                                      │
│     Encrypted with: EncryptionService      │
│                                            │
│  5. Store in User.encrypted_identity_key   │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  User Record Now Contains:                 │
│                                            │
│  principal_id: "rrkah-fqaaa-..."           │
│  account_id: "0x1234...abcd"               │
│  encrypted_identity_key: "{encrypted}"     │
│  identity_created_at: datetime.utcnow()    │
│  wallet_cycles_balance: "0"                │
└────────────────────────────────────────────┘

Later, when deploying:
┌────────────────────────────────────────────┐
│  Deployment Request:                       │
│  POST /deployments/projects/123/deploy     │
│                                            │
│  1. get_current_user_id(token) -> 42       │
│  2. get_project(123, user_id=42) -> OK     │
│  3. DeploymentService.deploy_project()     │
│  4. Fetch user (user_id=42)                │
│  5. ICPIdentityManager.get_user_identity_context(user)
│     - Decrypt encrypted_identity_key       │
│     - Restore .dfx/identity/ files         │
│  6. ICPIdentityManager.switch_to_user_identity(user)
│     - Sets dfx CLI to use user's identity  │
│  7. DfxCommand.canisterCreate(...)         │
│     (Creates canister with user as         │
│      controller via their identity)        │
│  8. Update Project.canister_id             │
│     Update Project.principal_id            │
└────────────────────────────────────────────┘
```

---

### 8.5 Authorization: Role-Based Access

```
┌─────────────────────────────────────────────┐
│  User A requests to update Project X        │
│                                             │
│  PUT /api/v1/projects/100                   │
│  Authorization: Bearer {user_a_token}       │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│  Dependency: get_current_user_id            │
│  Returns: user_a_id = 42                    │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│  Route: update_project(project_id=100, user_id=42)
│                                             │
│  1. Call ProjectService.get_project_by_id(  │
│       session,                              │
│       project_id=100,                       │
│       user_id=42  <- OWNERSHIP CHECK        │
│     )                                       │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│  SQL Query:                                 │
│  SELECT * FROM projects                    │
│  WHERE id = 100                             │
│    AND user_id = 42  <- Key constraint      │
└─────────┬───────────────────────────────────┘
          │
          ├─ User A is owner -> Returns Project
          │  (proceed with update)
          │
          └─ User A is NOT owner -> Returns NULL
             (raise 404 "Not Found")
             (Never exposes that project exists)
```

---

### 8.6 Authorization: RBAC (Future Enhancement)

```
Current: Binary ownership (user_id = owner)

Future: ProjectEnrollment-based RBAC

┌──────────────────────────────────────────┐
│  User A (owner) invites User B (editor)   │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  INSERT ProjectEnrollment                 │
│  (user_id=B_id, project_id=100, role='editor')
│                                          │
│  Now User B can:                         │
│  - Read project details (role=viewer+)   │
│  - Edit code (role=editor+)              │
│  - Deploy (role=editor+)                 │
│  - NOT delete (role=admin+ only)         │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  When User B requests: PUT /projects/100  │
│                                          │
│  1. Check User B owns project 100        │
│     OR                                   │
│  2. Check ProjectEnrollment where        │
│     user_id = B_id                       │
│     AND project_id = 100                 │
│     AND role IN ('admin', 'editor')      │
│                                          │
│  If neither: 403 Forbidden               │
└──────────────────────────────────────────┘
```

---

## 9. SUMMARY OF CRITICAL FINDINGS

### What Must Be Ported to Motoko

1. **User Management** (83 LOC service)
   - Registration with email verification
   - Password reset workflow
   - Profile storage
   - ICP identity lifecycle (already integrated)

2. **Project Management** (107 LOC service)
   - CRUD operations with deterministic URLs
   - Ownership verification
   - Deployment status tracking
   - Multi-user enrollment (RBAC)

3. **Deployment Orchestration** (215 LOC service)
   - Canister creation coordination
   - Code deployment and versioning
   - Status tracking through async operations
   - Error handling and retry logic

4. **Domain Management** (482 LOC service)
   - Custom domain configuration
   - DNS verification coordination
   - SSL certificate tracking
   - ICP boundary node registration

5. **Wallet Management** (combined 388+461 LOC)
   - ICP balance tracking
   - Cycles balance coordination
   - Funding requirement checks
   - Auto-conversion logic

### What Can Stay in Backend (if hybrid architecture)

1. **Email notifications** (external service)
2. **Token/email verification** (if centralized)
3. **API gateway & rate limiting** (edge layer)
4. **Rosetta API integration** (if not moved to Canister)
5. **DNS resolution calls** (off-chain HTTP outcalls)

### Key Challenges for Motoko

1. **Reverse Indices**: No unique constraints → need HashMap reverse indexes
2. **Large State**: Metrics table grows unbounded → need circular buffer strategy
3. **HTTP Outcalls**: DNS & boundary node calls → use canister HTTP outcalls
4. **Token Verification**: JWT validation → move to frontend or gateway
5. **Inter-canister calls**: Add retry logic and circuit breaker patterns
6. **Data Migration**: Snapshot Python DB → transform → batch load to Motoko

---

## 10. DEVELOPMENT ROADMAP (Recommended)

**Phase 1** (Weeks 1-2): Core Infrastructure
- [ ] Deploy 7 empty canisters (allocate cycles)
- [ ] Implement Users canister (registration, profiles)
- [ ] Implement Projects canister (CRUD, ownership)
- [ ] Set up inter-canister communication patterns
- [ ] Add retry/resilience logic

**Phase 2** (Weeks 3-4): Deployment & Infrastructure
- [ ] Implement Deployments canister
- [ ] Integrate Management canister API
- [ ] Test canister creation
- [ ] Implement status tracking

**Phase 3** (Weeks 5-6): Advanced Features
- [ ] Implement Domains canister
- [ ] Implement Wallet canister
- [ ] Implement Metrics canister
- [ ] HTTP outcalls for DNS & boundary nodes

**Phase 4** (Week 7): Testing & Migration
- [ ] End-to-end testing
- [ ] Data migration scripts
- [ ] Parallel running (write to both)
- [ ] DNS cutover

**Phase 5** (Week 8): Cutover & Monitoring
- [ ] Switch to Motoko backend
- [ ] Monitor for issues
- [ ] Sunset Python backend (keep for 30 days)

---
