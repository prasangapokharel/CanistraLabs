# Canistra Development Agent Guidelines

## Code Standards

### Naming Conventions

#### Backend (Python)
- **Files**: `snake_case` (e.g., `auth.py`, `email_verification.py`)
- **Classes**: `PascalCase` (e.g., `User`, `AuthService`, `PasswordResetService`)
- **Functions/Methods**: `snake_case` (e.g., `get_user`, `create_token`, `send_email`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Variables**: `snake_case` (e.g., `user_id`, `token_expiry`, `refresh_token`)
- **Database Columns**: `snake_case` (e.g., `email_verified`, `password_hash`, `created_at`)

#### Frontend (TypeScript/React)
- **Files**: `camelCase` or `PascalCase` based on content
  - Components: `PascalCase` (e.g., `PageBreadcrumbs.tsx`, `HelpTooltip.tsx`)
  - Utilities/Hooks: `camelCase` (e.g., `useBreadcrumbs.ts`, `usePasswordStrength.ts`)
  - Libraries: `camelCase` (e.g., `apiClient.ts`, `helpTexts.ts`)
- **Classes/Types**: `PascalCase` (e.g., `AuthContextType`, `ProjectMetrics`)
- **Functions/Methods**: `camelCase` (e.g., `handleSubmit`, `fetchProjects`, `formatCycles`)
- **Constants**: `UPPER_SNAKE_CASE` for config, `camelCase` for derived (e.g., `MAX_RETRIES`, `sortByDate`)
- **Variables**: `camelCase` (e.g., `isLoading`, `userId`, `projectName`)

### Code Style

#### No Docstrings
- Remove all docstring comments (`"""..."""` in Python, `/**...**/` in TypeScript)
- Comments are only used for **critical business logic clarification** when intent is not obvious
- Example of acceptable comment:
  ```python
  # Proactive refresh 5 minutes before expiry prevents logout
  await apiClient.proactiveTokenRefresh()
  ```

#### No Duplicate Comments
- Never repeat what the code already says
- Bad: `user_id = 1  # Set user ID to 1`
- Good: No comment needed (code is self-explanatory)
- Good: `user_id = 1  # Hardcoded for local testing`

#### Clean Minimal Code
- One responsibility per function
- Remove unused imports immediately
- Keep functions under 30 lines
- Use semantic variable names that explain intent
- No nested ternaries or complex expressions
- Prefer explicit over implicit

### File Organization

#### Backend Structure
```
backend/
├── app/
│   ├── api/v1/
│   │   ├── auth.py                  # Authentication endpoints
│   │   ├── projects.py              # Project management
│   │   ├── deployments.py           # Deployment operations
│   │   ├── metrics.py               # Metrics collection
│   │   ├── wallet.py                # Wallet/cycles management
│   │   ├── domainManagement.py      # Custom domains (RENAME: domain.py)
│   │   └── ...
│   ├── models/
│   │   ├── user.py                  # User model
│   │   ├── project.py               # Project model
│   │   ├── deployment.py            # Deployment model
│   │   ├── canister.py              # Canister model
│   │   └── ...
│   ├── schemas/
│   │   ├── user.py                  # User request/response schemas
│   │   ├── project.py               # Project schemas
│   │   └── responses.py             # Common response schemas
│   ├── services/
│   │   ├── auth.py                  # Authentication business logic
│   │   ├── projects.py              # Project business logic
│   │   ├── password_reset.py        # Password reset logic
│   │   ├── email_verification.py    # Email verification logic
│   │   └── ...
│   ├── utils/
│   │   ├── security.py              # Token/password utilities
│   │   ├── rate_limit.py            # Rate limiting
│   │   └── ...
│   └── database/
│       ├── db.py                    # Database setup
│       └── init.py                  # Database initialization
├── tests/
└── main.py                          # FastAPI app entry
```

#### Frontend Structure
```
frontend/src/
├── app/                             # Next.js App Router pages
│   ├── login/
│   ├── signup/
│   ├── dashboard/
│   │   ├── projects/
│   │   ├── billing/
│   │   ├── analytics/
│   │   ├── settings/
│   │   └── ...
│   └── ...
├── components/
│   ├── ui/                          # shadcn/ui components
│   ├── auth/                        # Auth forms
│   ├── dashboard/                   # Dashboard components
│   ├── landing/                     # Landing page components
│   └── ...
├── hooks/                           # Custom React hooks
│   ├── useBreadcrumbs.ts
│   ├── usePasswordStrength.ts
│   ├── api/                         # API integration hooks
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   └── ...
│   └── ...
├── lib/                             # Utilities & libraries
│   ├── apiClient.ts                 # HTTP client
│   ├── api.ts                       # API endpoints wrapper
│   ├── toast.ts                     # Toast notifications
│   ├── validations.ts               # Zod schemas
│   ├── helpTexts.ts                 # Help text definitions
│   ├── utils.ts                     # Generic utilities
│   ├── localStorage.ts              # LocalStorage wrapper
│   └── ...
├── providers/                       # React context providers
│   ├── AuthProvider.tsx
│   └── ...
├── types/
│   ├── api.ts                       # API response types
│   └── ...
├── styles/
│   └── globals.css                  # Global styles
└── middleware.ts                    # Next.js middleware
```

### DFX Official Commands

Always use official `dfx` CLI for ICP interactions:

```bash
# Deploy canister
dfx deploy <canister-name>

# Build canister
dfx build <canister-name>

# Call canister method
dfx canister call <canister-name> <method-name> <args>

# View logs
dfx canister logs <canister-name>

# Get canister status
dfx canister status <canister-name>

# Stop canister
dfx stop <canister-name>

# Start canister
dfx start

# Check version
dfx --version
```

### API Design Pattern

#### Request/Response Structure
```typescript
// Request
POST /api/v1/projects
{
  name: string
  description?: string
  language: string
}

// Response (Success)
{
  success: true
  data: {
    id: number
    name: string
    status: string
    createdAt: string
  }
}

// Response (Error)
{
  success: false
  error: string
  statusCode: number
}
```

#### Backend FastAPI Route Pattern
```python
@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def createProject(
  request: ProjectCreate,
  session: AsyncSession = Depends(get_db),
  currentUser = Depends(get_current_user)
) -> ProjectResponse:
  project = await ProjectService.create(request, currentUser.id, session)
  return ProjectResponse.from_orm(project)
```

#### Frontend Hook Pattern
```typescript
export function useCreateProject() {
  return useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.list() })
      toast.success('Project created successfully')
    },
    onError: (error) => {
      toast.error(handleApiError(error))
    }
  })
}
```

### Error Handling

#### Backend (FastAPI)
```python
class ApiError(HTTPException):
  def __init__(self, message: str, status_code: int = 400):
    super().__init__(status_code=status_code, detail=message)

# Usage
if not user:
  raise ApiError("User not found", status.HTTP_404_NOT_FOUND)
```

#### Frontend
```typescript
function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.error || 'An error occurred'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unknown error'
}

// Usage
try {
  await api.post(...)
} catch (error) {
  toast.error(handleApiError(error))
}
```

### Authentication Flow

#### Backend Implementation
1. User signs up → `AuthService.signup()` → JWT tokens created
2. Token refresh → `AuthService.refreshToken()` → New access token issued
3. Protected routes → `get_current_user()` dependency → Extract & validate JWT
4. Logout → Invalidate token in Redis (optional, client-side works)

#### Frontend Implementation
1. Login form → `useAuth().login()` → Access/refresh tokens stored
2. Auto-refresh → `AuthProvider` checks token expiry → Refresh if needed
3. Protected routes → `useAuth()` hook → Redirect to login if unauthenticated
4. Logout → Clear tokens → Redirect to login

### Database Patterns

#### Models (SQLAlchemy ORM)
```python
class Project(Base):
  __tablename__ = "projects"
  
  id: Mapped[int] = mapped_column(primary_key=True)
  userId: Mapped[int] = mapped_column(ForeignKey("users.id"))
  name: Mapped[str] = mapped_column(String(255), nullable=False)
  status: Mapped[str] = mapped_column(String(50), default="draft")
  createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  
  user: Mapped[User] = relationship(back_populates="projects")
```

#### Schemas (Pydantic)
```python
class ProjectCreate(BaseModel):
  name: str
  description: Optional[str] = None
  language: str

class ProjectResponse(BaseModel):
  id: int
  name: str
  status: str
  createdAt: datetime
  
  class Config:
    from_attributes = True
```

### Testing Pattern

#### Backend (pytest)
```python
@pytest.mark.asyncio
async def test_createProject_success(db_session: AsyncSession):
  user = await UserFactory.create(db_session)
  data = ProjectCreate(name="Test", language="rust")
  
  project = await ProjectService.create(data, user.id, db_session)
  
  assert project.name == "Test"
  assert project.userId == user.id
```

#### Frontend (Vitest/React Testing Library)
```typescript
describe('useCreateProject', () => {
  it('should create project successfully', async () => {
    const { result } = renderHook(() => useCreateProject())
    
    act(() => {
      result.current.mutate({ name: 'Test', language: 'rust' })
    })
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
  })
})
```

### Performance Best Practices

#### Backend
- Use pagination for list endpoints (default 20, max 100)
- Add database indexes on foreign keys and search fields
- Use connection pooling (default: min=5, max=20)
- Cache frequently accessed data (Redis for sessions/tokens)
- Implement rate limiting (10 requests/second per user)

#### Frontend
- Use React Query for state management (auto caching, deduplication)
- Code splitting for routes with `React.lazy()`
- Image optimization with `next/image`
- Memoization for expensive computations
- Virtual scrolling for large lists

### Security

#### Backend
- Validate all inputs with Pydantic schemas
- Hash passwords with Argon2 (fastapi-users)
- JWT tokens with 15-minute expiry
- Refresh tokens with 7-day expiry
- CORS enabled only for frontend origin
- SQL injection prevention via ORM
- Rate limiting on auth endpoints (3 requests/minute per IP)

#### Frontend
- Store tokens in httpOnly cookies (if possible) or secure localStorage
- Never expose sensitive data in logs
- Validate user input before sending
- CSRF protection via SameSite cookies
- Content Security Policy headers

### Monitoring & Logging

#### Backend
```python
logger.info(f"Project created: {project.id}")
logger.warning(f"High memory usage: {memory_percent}%")
logger.error(f"Database connection failed", exc_info=True)
```

#### Frontend
```typescript
logger.info('User logged in', { userId: user.id })
logger.warn('API response slow', { duration: 5000 })
logger.error('Request failed', error)
```

## Development Workflow

### Git Commits
```
feat: Add project creation API
fix: Resolve token refresh infinite loop
refactor: Extract authentication logic to service
docs: Update API documentation
test: Add unit tests for password validation
chore: Update dependencies
```

### PR Checklist
- [ ] Code follows naming conventions
- [ ] No docstrings (only critical comments)
- [ ] No duplicate/obvious comments
- [ ] All imports used
- [ ] Functions under 30 lines
- [ ] Error handling implemented
- [ ] Tests pass
- [ ] No secrets in code

### Code Review Criteria
1. **Naming**: Are names clear and follow conventions?
2. **Comments**: Are comments necessary and non-redundant?
3. **Logic**: Is the code doing one thing well?
4. **Errors**: Are errors handled appropriately?
5. **Tests**: Is the change testable and tested?

## DFX Integration

### Deploying Canisters
```bash
# Development
dfx deploy --network ic

# Check deployment
dfx canister info <canister-name> --network ic

# Verify functionality
dfx canister call <canister-name> greet "Alice" --network ic
```

### Local Development
```bash
# Start local replica
dfx start

# Deploy locally
dfx deploy

# Reset state
dfx stop
dfx start --clean
```

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DFX_NETWORK=ic
DATABASE_URL=postgresql://user:pass@localhost/canistra
```

## Common Patterns

### API Client Usage
```typescript
// Simple request
const user = await apiClient.get('/users/me')

// With error handling
try {
  const data = await apiClient.post('/projects', projectData)
} catch (error) {
  throw new Error(handleApiError(error))
}

// With retry
const data = await apiClient.get('/projects', { retry: 3 })
```

### Form Handling
```typescript
const form = useForm<ProjectCreate>({
  resolver: zodResolver(projectCreateSchema),
  defaultValues: { name: '', language: 'rust' }
})

const onSubmit = async (data: ProjectCreate) => {
  try {
    await createProjectMutation.mutateAsync(data)
  } catch (error) {
    form.setError('root', { message: handleApiError(error) })
  }
}
```

### Query Management
```typescript
// Fetch list
const { data: projects } = useQuery({
  queryKey: queryKeys.projects.list(),
  queryFn: projectsApi.getList
})

// Invalidate cache after mutation
queryClient.invalidateQueries({ queryKey: queryKeys.projects.list() })
```

## Prohibited Patterns

1. ❌ Docstrings (`"""..."""` or `/**...*/`)
2. ❌ Obvious comments (`// Set x to 5`)
3. ❌ Functions over 30 lines
4. ❌ Complex nested ternaries
5. ❌ `any` types in TypeScript
6. ❌ Global state (use React Query + Context)
7. ❌ Direct DOM manipulation (use React)
8. ❌ Hardcoded secrets or API keys
9. ❌ Magic numbers without explanation
10. ❌ Unused imports

## Resources

- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy 2.0: https://docs.sqlalchemy.org
- Next.js 14: https://nextjs.org/docs
- React Query: https://tanstack.com/query
- shadcn/ui: https://ui.shadcn.com
- DFX: https://internetcomputer.org/docs/current/developer-docs/build/install-upgrade
- TypeScript: https://www.typescriptlang.org/docs
- Python: https://docs.python.org/3
