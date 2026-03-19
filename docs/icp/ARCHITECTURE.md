# Architecture Guide

Complete system design and architecture documentation for the Internet Computer Hosting Platform.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Data Models](#data-models)
4. [API Design](#api-design)
5. [Service Layer](#service-layer)
6. [Authentication & Security](#authentication--security)
7. [Database Design](#database-design)
8. [ICP Integration](#icp-integration)
9. [Deployment Architecture](#deployment-architecture)
10. [Data Flow](#data-flow)

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
│  (Web Browser, Mobile App, CLI, API Consumers)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS/HTTP
                         │
┌────────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Python 3.14)                   │
│                    http://localhost:8000                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           API Router Layer (APIRoutes)                │ │
│  │                                                        │ │
│  │  • /api/v1/auth      (login, signup, refresh)         │ │
│  │  • /api/v1/projects  (CRUD operations)                │ │
│  │  • /api/v1/deployments (deploy to ICP)                │ │
│  └────────────────────────────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────────┐ │
│  │         Service Layer (Business Logic)                 │ │
│  │                                                        │ │
│  │  • AuthService (JWT, password hashing)                │ │
│  │  • ProjectsService (CRUD, ownership checks)           │ │
│  │  • DeploymentService (dfx integration)                │ │
│  └────────────────────────────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────────┐ │
│  │      Data Layer (SQLAlchemy ORM)                      │ │
│  │                                                        │ │
│  │  Models: User, Project, Canister, Deployment          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────┬──────────────────────┬──────────────────────┬─────┘
           │                      │                      │
           │ SQL                  │ Shell Commands       │
           │                      │                      │
    ┌──────▼──┐          ┌────────▼────────┐      ┌────▼────┐
    │ Database│          │  dfx Command    │      │ICP      │
    │(SQLite/ │          │  Line (v0.31.0) │      │Canister │
    │PostgreSQL)         │                 │      │Service  │
    └──────────┘         └────────┬────────┘      └─────────┘
                                  │
                         ┌────────▼────────┐
                         │  dfx Replica    │
                         │ (local:4943)    │
                         └─────────────────┘
```

### Request Flow

```
1. Client Request
   │
   ├─ POST /api/v1/auth/login
   │
2. FastAPI Router
   │
   ├─ Routes to endpoint handler
   │
3. Endpoint Handler
   │
   ├─ Validates request (Pydantic schemas)
   ├─ Checks authentication (JWT token)
   │
4. Service Layer
   │
   ├─ Implements business logic
   ├─ Queries database (SQLAlchemy)
   │
5. Database Query
   │
   ├─ Execute SQL query
   ├─ Return results
   │
6. Response Processing
   │
   ├─ Format response (Pydantic)
   ├─ Return to client
   │
7. Client Response
   ├─ HTTP 200 + JSON body
```

## Technology Stack

### Backend Framework

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | FastAPI | Latest | Modern async API framework |
| **Server** | Uvicorn | Latest | ASGI server for FastAPI |
| **Python** | Python | 3.14+ | Runtime |

### Database

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Async** | asyncpg/aiosqlite | Latest | Async database drivers |
| **Local Dev** | SQLite | Built-in | Easy local development |
| **Production** | PostgreSQL | 12+ | Production database |

### Authentication & Security

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **JWT** | PyJWT | Token-based authentication |
| **Hashing** | bcrypt | Secure password hashing |
| **Validation** | Pydantic | Request/response validation |

### ICP Integration

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **dfx SDK** | dfx | 0.31.0+ | Canister deployment |
| **Asset Format** | HTML/CSS/JS | Native | Frontend hosting |
| **Network** | Internet Computer | Mainnet/Local | Decentralized hosting |

### Testing

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Test Framework** | pytest | Latest | Unit and integration tests |
| **Async Testing** | pytest-asyncio | Latest | Async test support |
| **Coverage** | pytest-cov | Latest | Code coverage reporting |
| **HTTP Client** | httpx | Latest | Async HTTP testing |

## Data Models

### User Model

```python
class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    # Primary Key
    id: UUID = Column(UUID, primary_key=True)
    
    # Authentication
    email: str = Column(String(255), unique=True, nullable=False)
    username: str = Column(String(100), nullable=False)
    hashed_password: str = Column(String(255), nullable=False)
    
    # Metadata
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
    updated_at: DateTime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projects: List[Project] = relationship("Project", back_populates="owner")
```

**Relationships**:
- User → Projects (one-to-many)

**Constraints**:
- Email is unique
- Username is required
- Password is hashed (never stored in plaintext)

### Project Model

```python
class Project(Base):
    """Project model for organizing deployments"""
    __tablename__ = "projects"
    
    # Primary Key
    id: UUID = Column(UUID, primary_key=True)
    
    # Content
    name: str = Column(String(255), nullable=False)
    description: str = Column(String(1000), nullable=True)
    
    # Ownership
    owner_id: UUID = Column(UUID, ForeignKey("users.id"))
    
    # Metadata
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
    updated_at: DateTime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner: User = relationship("User", back_populates="projects")
    deployments: List[Deployment] = relationship("Deployment")
```

**Constraints**:
- Owner must be a valid user
- Name is required
- Project is owned by exactly one user

### Canister Model

```python
class Canister(Base):
    """ICP canister information"""
    __tablename__ = "canisters"
    
    # Primary Key
    id: UUID = Column(UUID, primary_key=True)
    
    # Canister Info
    canister_id: str = Column(String(255), unique=True, nullable=False)
    network: str = Column(String(50), nullable=False)  # "local" or "ic"
    
    # Status
    status: str = Column(String(50), default="active")
    
    # Metadata
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deployments: List[Deployment] = relationship("Deployment")
```

**Constraints**:
- Canister ID is globally unique
- Network is either "local" or "ic"
- Status tracks canister health

### Deployment Model

```python
class Deployment(Base):
    """Project deployment to ICP"""
    __tablename__ = "deployments"
    
    # Primary Key
    id: UUID = Column(UUID, primary_key=True)
    
    # References
    project_id: UUID = Column(UUID, ForeignKey("projects.id"))
    canister_id: UUID = Column(UUID, ForeignKey("canisters.id"))
    
    # Deployment Info
    status: str = Column(String(50), default="success")  # success, pending, failed
    deployment_url: str = Column(String(1000), nullable=True)
    
    # Content
    html_content: str = Column(Text, nullable=True)
    
    # Metadata
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
    updated_at: DateTime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project: Project = relationship("Project")
    canister: Canister = relationship("Canister")
```

**Constraints**:
- Project and canister must exist
- Status indicates deployment state
- URL built from canister ID

### Entity-Relationship Diagram

```
┌──────────┐         ┌──────────┐
│  User    │         │ Canister │
├──────────┤         ├──────────┤
│ id (PK)  │────┐    │ id (PK)  │
│ email    │    │    │ canister_id
│ username │    │    │ network  │
│ password │    │    │ status   │
└──────────┘    │    └──────────┘
                │           ▲
                │           │
           ┌────▼───────────┼───┐
           │  Project      │    │
           ├───────────────┼────┤
           │ id (PK)       │    │
           │ owner_id (FK) │    │
           │ name          │    │
           └───────────────┘    │
                │                │
                │ ┌──────────────┘
                │ │
           ┌────▼─▼────┐
           │Deployment │
           ├────────────┤
           │ id (PK)    │
           │ project_id │
           │ canister_id│
           │ status     │
           └────────────┘
```

## API Design

### REST Endpoints

#### Auth Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/v1/auth/signup` | Register new user | None |
| POST | `/api/v1/auth/login` | Login with credentials | None |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | Refresh token |

#### Project Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/v1/projects` | List user's projects | JWT |
| POST | `/api/v1/projects` | Create new project | JWT |
| GET | `/api/v1/projects/{id}` | Get project details | JWT |
| PUT | `/api/v1/projects/{id}` | Update project | JWT |
| DELETE | `/api/v1/projects/{id}` | Delete project | JWT |

#### Deployment Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/v1/deployments` | Deploy project | JWT |
| GET | `/api/v1/deployments` | List deployments | JWT |
| GET | `/api/v1/deployments/{id}` | Get deployment status | JWT |
| GET | `/api/v1/deployments/{id}/logs` | Get deployment logs | JWT |

### Response Format

All API responses follow a consistent format:

```json
{
  "data": {
    // Response payload or null
  },
  "status": "success|error",
  "message": "Human readable message"
}
```

**Example Success**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "john_doe"
  },
  "status": "success",
  "message": "User created successfully"
}
```

**Example Error**:
```json
{
  "data": null,
  "status": "error",
  "message": "Email already registered"
}
```

## Service Layer

### AuthService

Handles user authentication and JWT management.

```python
class AuthService:
    async def signup(
        email: str,
        password: str,
        username: str
    ) -> User:
        """Create new user account"""
        # 1. Validate input
        # 2. Hash password
        # 3. Create user
        # 4. Return user with tokens
    
    async def login(
        email: str,
        password: str
    ) -> User:
        """Authenticate user"""
        # 1. Find user by email
        # 2. Verify password
        # 3. Generate tokens
        # 4. Return user
    
    def create_access_token(user_id: UUID) -> str:
        """Generate JWT access token"""
        # Expires in 30 minutes
    
    def create_refresh_token(user_id: UUID) -> str:
        """Generate JWT refresh token"""
        # Expires in 7 days
```

### ProjectService

Manages project CRUD operations.

```python
class ProjectService:
    async def create_project(
        owner_id: UUID,
        name: str,
        description: str
    ) -> Project:
        """Create new project"""
    
    async def get_project(
        project_id: UUID,
        owner_id: UUID
    ) -> Project:
        """Get project if user owns it"""
    
    async def list_projects(owner_id: UUID) -> List[Project]:
        """List all projects for user"""
    
    async def update_project(
        project_id: UUID,
        owner_id: UUID,
        **updates
    ) -> Project:
        """Update project if user owns it"""
    
    async def delete_project(
        project_id: UUID,
        owner_id: UUID
    ) -> bool:
        """Delete project if user owns it"""
```

### DeploymentService

Handles deployment to Internet Computer.

```python
class DeploymentService:
    async def deploy_project(
        project_id: UUID,
        html_content: str,
        network: str = "local"
    ) -> Deployment:
        """Deploy project to ICP"""
        # 1. Find or create canister
        # 2. Write HTML to filesystem
        # 3. Call dfx deploy
        # 4. Create deployment record
        # 5. Return deployment info
    
    async def get_deployment_status(
        deployment_id: UUID
    ) -> Deployment:
        """Get current deployment status"""
    
    async def get_deployment_logs(
        deployment_id: UUID
    ) -> str:
        """Get deployment logs from dfx"""
```

## Authentication & Security

### JWT Token Flow

```
1. User Login/Signup
   │
   ├─ Password verified/hashed
   │
2. Generate Tokens
   │
   ├─ Access Token (30 min, short-lived)
   ├─ Refresh Token (7 days, long-lived)
   │
3. Return to Client
   │
   ├─ Store access token in memory
   ├─ Store refresh token in secure cookie
   │
4. API Requests
   │
   ├─ Include access token in Authorization header
   ├─ Authorization: Bearer <access_token>
   │
5. Token Expiration
   │
   ├─ Access token expires after 30 minutes
   │
6. Token Refresh
   │
   ├─ Use refresh token to get new access token
   ├─ POST /api/v1/auth/refresh
   ├─ Return new access token
```

### Password Security

- Passwords are hashed using **bcrypt** with salt
- Plain text passwords never stored in database
- Minimum 8 characters recommended
- Users cannot see their own password

```python
# Password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# Hash password
hashed = pwd_context.hash(password)

# Verify password
is_valid = pwd_context.verify(password, hashed)
```

### Request Validation

All API requests validated using Pydantic:

```python
class SignupRequest(BaseModel):
    email: EmailStr  # Must be valid email
    password: str    # At least 8 chars
    username: str    # Non-empty
```

### CORS Configuration

Configure allowed origins for cross-origin requests:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Database Design

### SQLAlchemy ORM

All models inherit from declarative base:

```python
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    # ... columns ...
```

### Async Database Operations

All database operations are async for non-blocking I/O:

```python
# Get database session
async with AsyncSession(engine) as session:
    # Query
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    # Create
    new_user = User(email="user@example.com")
    session.add(new_user)
    await session.commit()
```

### Database Indexes

Key indexes for performance:

```python
class User(Base):
    __tablename__ = "users"
    
    # Fast lookups by email
    email: str = Column(String(255), unique=True, index=True)
    
class Project(Base):
    __tablename__ = "projects"
    
    # Fast lookups by owner
    owner_id: UUID = Column(UUID, ForeignKey("users.id"), index=True)
```

## ICP Integration

### dfx Command Execution

The platform integrates with dfx SDK to deploy to Internet Computer:

```python
import subprocess
import os

async def deploy_to_icp(
    html_content: str,
    project_name: str,
    network: str = "local"
) -> str:
    """
    Deploy HTML to ICP canister using dfx
    
    1. Write HTML to canister directory
    2. Execute: dfx deploy <canister> --network <network>
    3. Extract canister ID from output
    4. Return deployment URL
    """
    
    # Set environment
    env = os.environ.copy()
    env['DFX_WARNING'] = '-mainnet_plaintext_identity'
    
    # Find dfx binary
    dfx_path = "~/.local/bin/dfx"
    
    # Execute deployment
    result = subprocess.run(
        [dfx_path, "deploy", "portfolio", f"--network={network}"],
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Deployment failed: {result.stderr}")
    
    return extract_canister_id(result.stdout)
```

### Canister Model

Internet Computer uses **asset canisters** for HTML hosting:

```
┌─────────────────────────────────────────┐
│        Asset Canister (Wasm)            │
├─────────────────────────────────────────┤
│                                         │
│  • Stores static HTML/CSS/JS files      │
│  • Serves via HTTP Gateway              │
│  • Immutable after deployment           │
│  • Costs cycles proportional to size    │
│                                         │
│  Example URL:                           │
│  https://<canister_id>.ic0.app          │
│                                         │
└─────────────────────────────────────────┘
```

### Deployment Process

```
1. User Uploads HTML
   │
   ├─ Content stored in request
   │
2. Backend Receives Request
   │
   ├─ Validate HTML content
   ├─ Create deployment record
   │
3. Write to Canister Directory
   │
   ├─ Write HTML to: portfolio/index.html
   │
4. Execute dfx deploy
   │
   ├─ Run: dfx deploy portfolio --network local
   │
5. Extract Canister ID
   │
   ├─ Parse output: "portfolio: [canister_id]"
   │
6. Build Access URL
   │
   ├─ Local: http://localhost:4943/?canisterId=<id>
   ├─ Mainnet: https://<id>.ic0.app
   │
7. Save to Database
   │
   ├─ Store deployment record
   ├─ Return to client
```

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────────┐
│       Local Development Environment     │
├─────────────────────────────────────────┤
│                                         │
│  Backend API          dfx Replica      │
│  Port: 8000           Port: 4943       │
│                                        │
│  ┌─────────────┐    ┌──────────────┐  │
│  │  FastAPI    │◄──►│ Asset        │  │
│  │  Server     │    │ Canister     │  │
│  └─────────────┘    │ (Local)      │  │
│                     └──────────────┘  │
│                                        │
│  Database: SQLite (test.db)           │
│                                        │
└─────────────────────────────────────────┘
```

### Production (IC Mainnet)

```
┌──────────────────────────────────────────────┐
│        Internet Computer Mainnet             │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  Portfolio Canister (Asset)            │ │
│  │                                        │ │
│  │  Canister ID:                          │ │
│  │  qjtxq-xaaaa-aaaae-ada4q-cai          │ │
│  └────────────────────────────────────────┘ │
│            │                                 │
│            ▼                                 │
│  ┌────────────────────────────────────────┐ │
│  │  HTTPS Gateway (ic0.app)              │ │
│  │                                        │ │
│  │  URL: https://<canister_id>.ic0.app   │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  Backend Service (Optional)            │ │
│  │  - User authentication                │ │
│  │  - Project management                 │ │
│  │  - Deployment orchestration           │ │
│  └────────────────────────────────────────┘ │
│                                              │
└──────────────────────────────────────────────┘
```

## Data Flow

### Complete Request Flow: User Signup → Create Project → Deploy

```
1. User Signup
   ┌──────────────┐
   │ POST /signup │
   └──────┬───────┘
          │
   ┌──────▼──────────────────────────┐
   │ Validate email, password         │
   │ (Pydantic schema)                │
   └──────┬──────────────────────────┘
          │
   ┌──────▼──────────────────────────┐
   │ Hash password (bcrypt)           │
   │ Create user record in database   │
   └──────┬──────────────────────────┘
          │
   ┌──────▼──────────────────────────┐
   │ Generate JWT tokens              │
   │ - Access: 30 min                 │
   │ - Refresh: 7 days                │
   └──────┬──────────────────────────┘
          │
   ┌──────▼──────────────────────────┐
   │ Return user + tokens to client   │
   └──────────────────────────────────┘

2. Create Project
   ┌─────────────────────────────┐
   │ POST /projects              │
   │ Header: Authorization: JWT  │
   └─────────┬───────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Verify JWT token               │
   │ Extract user_id from token     │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Validate project input         │
   │ (name, description)            │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Create project record          │
   │ owner_id = current user        │
   │ Save to database               │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Return project ID to client    │
   └────────────────────────────────┘

3. Deploy Project
   ┌────────────────────────────┐
   │ POST /deployments          │
   │ - project_id               │
   │ - html_content             │
   │ - network (local or ic)    │
   └─────────┬──────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Verify JWT token               │
   │ Verify project ownership       │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Get or create canister         │
   │ (if not exists)                │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Write HTML to portfolio/        │
   │ index.html                      │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Execute dfx deploy              │
   │ subprocess call to dfx binary   │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Parse dfx output for ID         │
   │ Extract canister_id             │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Build deployment URL            │
   │ Local: http://...?canisterId=.. │
   │ IC: https://<id>.ic0.app        │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Save deployment record          │
   │ project_id, canister_id, url    │
   │ status = "success"              │
   └─────────┬──────────────────────┘
             │
   ┌─────────▼──────────────────────┐
   │ Return deployment info to user  │
   │ - deployment_id                 │
   │ - canister_id                   │
   │ - deployment_url                │
   └────────────────────────────────┘

4. Access Deployed Application
   ┌──────────────────────────────────┐
   │ User navigates to deployment_url  │
   └──────────┬───────────────────────┘
              │
   ┌──────────▼───────────────────────┐
   │ Browser requests HTML            │
   │ via IC HTTPS gateway             │
   └──────────┬───────────────────────┘
              │
   ┌──────────▼───────────────────────┐
   │ IC returns stored HTML from       │
   │ asset canister                   │
   └──────────┬───────────────────────┘
              │
   ┌──────────▼───────────────────────┐
   │ Browser renders HTML             │
   │ Content displayed to user        │
   └──────────────────────────────────┘
```

## Performance Characteristics

### Response Times

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Login | <50ms | Database lookup + JWT generation |
| Create Project | <30ms | Single database insert |
| List Projects | <100ms | Database query + serialization |
| Deploy (local) | 5-15s | dfx subprocess call |
| Deploy (mainnet) | 20-60s | Network latency + blockchain |

### Database Performance

- **Indexes on**: email (user lookup), owner_id (project filtering)
- **Connection pooling**: SQLAlchemy manages pool of connections
- **Async queries**: Non-blocking database operations
- **Query optimization**: Eager loading to prevent N+1 queries

### Scaling Considerations

1. **Horizontal Scaling**:
   - Run multiple FastAPI instances behind load balancer
   - Share PostgreSQL database
   - Use Redis for session/token caching

2. **Database Scaling**:
   - PostgreSQL read replicas for queries
   - Connection pooling (PgBouncer)
   - Sharding by user_id if needed

3. **Caching**:
   - Cache user profiles
   - Cache project listings
   - Cache deployment status

## Security Architecture

### Input Validation

```python
# All inputs validated via Pydantic
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)

# Prevents:
# - Oversized strings
# - Invalid types
# - SQL injection (auto-escaped)
```

### Authentication Flow

```
Client                                 Server
  │                                      │
  ├─ POST /auth/login ─────────────────►│
  │                                      │
  │◄─── JWT tokens ────────────────────┤
  │  (access + refresh)                 │
  │                                      │
  ├─ GET /api/v1/projects ────────────►│
  │  Authorization: Bearer <access>     │
  │                                      │
  │◄─── Protected resource ────────────┤
  │                                      │
  │  (After 30 min)                     │
  │                                      │
  ├─ POST /auth/refresh ──────────────►│
  │  Authorization: Bearer <refresh>    │
  │                                      │
  │◄─── New access token ──────────────┤
  │                                      │
  ├─ GET /api/v1/projects ────────────►│
  │  Authorization: Bearer <new_access> │
  │                                      │
  │◄─── Protected resource ────────────┤
```

### Authorization Checks

```python
# Only owner can access project
async def get_project(project_id: UUID, current_user: User) -> Project:
    project = await db.get(Project, project_id)
    
    # Check ownership
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403)  # Forbidden
    
    return project
```

## Monitoring & Observability

### Available Metrics

- Application logs (Uvicorn)
- Database query logs
- Request/response times
- Error tracking

### Debugging Support

```python
# Add debug logging
import logging

logger = logging.getLogger(__name__)

logger.debug(f"Deploying project {project_id}")
logger.info("Deployment successful")
logger.error(f"Deployment failed: {error}")
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }
```

---

This architecture provides a scalable, secure, and maintainable platform for hosting projects on Internet Computer.

For more information:
- See [README.md](README.md) for overview
- See [DEVELOPMENT.md](DEVELOPMENT.md) for development
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [API.md](API.md) for API reference
