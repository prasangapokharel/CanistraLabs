# ICP Hosting Platform - Quick Reference

## Key Statistics

| Metric | Value |
|--------|-------|
| Total API Endpoints | 55 |
| Service Modules | 12 (3,761 LOC) |
| Data Models | 8 core + 2 token models |
| Authentication | JWT (access + refresh) |
| Database | PostgreSQL with SQLAlchemy |
| Language | Python FastAPI |

## Data Models at a Glance

```
User
├── Projects (with Deployments, Canister, Metrics, CustomDomains)
├── ProjectEnrollments (RBAC: owner/admin/editor/viewer)
├── PasswordResetTokens
└── EmailVerificationTokens
```

## 12 Core Services

1. **AuthService** - User registration, login, password hashing
2. **ProjectService** - CRUD ops, URL generation, status tracking
3. **DeploymentService** - Deployment orchestration, status tracking
4. **ICPIdentityManager** - ICP identity creation and lifecycle
5. **CanisterFactory** - Individual canister creation per project
6. **DomainManagementService** - Custom domain setup, DNS config
7. **DfxCommand** - Low-level ICP CLI wrapper
8. **DynamicDeploymentService** - Dynamic deployment handling
9. **AutoFundingDetector** - Wallet balance checking
10. **RosettaClient** - Rosetta API integration for ICP ledger
11. **EmailVerificationService** - Email token lifecycle
12. **PasswordResetService** - Password reset token lifecycle

## API Routes Summary

- **Auth** (8): signup, login, refresh, logout, me, forgot-password, reset-password, verify-email
- **Projects** (5): CRUD + list
- **Deployments** (7): deploy, status, history
- **Wallet** (12): identity, balance, transfer, convert, funding
- **Domains** (8): setup, verify, status, register, delete
- **Metrics** (4): project metrics, live metrics, dashboard
- **Canister** (5): create, update, status, delete, DNS help
- **Cron** (3): start, stop, trigger, status

## Authentication Flow

```
1. Signup/Login → Generate JWT tokens (access + refresh)
2. Store in localStorage
3. Include in Authorization header: "Bearer {token}"
4. Middleware validates token, extracts user_id
5. Each endpoint checks ownership/permissions
```

## Key Business Logic to Port

**MUST PORT:**
1. User management (registration, profile)
2. Project CRUD (deterministic URLs)
3. Deployment orchestration (canister creation)
4. Custom domains (DNS + SSL)
5. Wallet management (balance tracking)

**CAN STAY IN BACKEND:**
- Email notifications
- Rosetta API integration (if not moved)
- Rate limiting (API gateway)
- DNS resolution calls

## ICP Integration Points

| Component | Purpose |
|-----------|---------|
| User.principal_id | User's ICP identity |
| User.account_id | ICP account for funding |
| User.encrypted_identity_key | Encrypted private key |
| Project.canister_id | Deployed canister ID |
| Project.principal_id | Canister controller |
| Deployment.task_id | Celery task tracking |

## Critical Database Constraints

- User.email + username (UNIQUE)
- Project.canister_id + url (UNIQUE)
- Canister.principal_id (UNIQUE)
- All relationships CASCADE on delete
- Token tables with expiry validation

## Recommended Motoko Architecture

7 Canisters:
1. **Users** - Registration, profiles (~100KB per 1000 users)
2. **Projects** - CRUD, ownership, enrollment (~1MB per 10K projects)
3. **Deployments** - Canister creation, code deployment (~500KB per 1000)
4. **Domains** - Custom domain config, DNS (~200KB per 1000 domains)
5. **Wallet** - Balance tracking, transfers (~50KB per 1000 users)
6. **Metrics** - Time-series data (1MB+ unbounded)
7. **Authorization** - RBAC verification (~100KB per 10K enrollments)

## Migration Strategy

1. **Phase 1** (2 weeks): Deploy empty canisters, Users + Projects
2. **Phase 2** (2 weeks): Deployments + Wallet
3. **Phase 3** (1 week): Domains + Metrics + Authorization
4. **Phase 4** (1 week): Testing + parallel running
5. **Phase 5** (ongoing): Monitor, sunset Python backend after 30 days

## Key Challenges for Motoko

- No UNIQUE constraints → Need reverse indices (HashMap)
- Metrics growth unbounded → Use circular buffer
- HTTP outcalls needed for DNS + boundary nodes
- Inter-canister calls need retry logic
- Token validation moves to API gateway
- Data migration from PostgreSQL

## Files to Review

- **Models**: `/backend/app/models/*.py` (8 files)
- **Services**: `/backend/app/services/*.py` (12 files)
- **APIs**: `/backend/app/api/v1/*.py` (8 routers)
- **Security**: `/backend/app/utils/security.py`
- **Config**: `/backend/app/config.py`

## Important URLs

- **Database**: PostgreSQL (async with SQLAlchemy)
- **Authentication**: JWT HS256 with 24h access token, 7d refresh
- **ICP Network**: Local or IC (configurable)
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000

---

Full analysis available in: **BACKEND_ANALYSIS.md** (1,911 lines)
