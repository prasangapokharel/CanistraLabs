# Code Standards Audit & Refactoring Plan

## Overview
AGENT.md has been created with comprehensive code standards. This document tracks findings and needed changes to align with these standards.

## Critical Findings

### Backend File Naming Issues (Priority: HIGH)

Files that need renaming to follow `snake_case` convention:

1. `/backend/app/api/v1/cleanDfx.py` → `clean_dfx.py`
2. `/backend/app/api/v1/domainManagement.py` → `domain_management.py`
3. `/backend/app/api/v1/dynamicDeployment.py` → `dynamic_deployment.py`
4. `/backend/app/models/projectMetrics.py` → `project_metrics.py`

Impact: Import statements in `__init__.py` and route registrations in `main.py` will need updates.

### Backend Docstrings (Priority: HIGH)

Files with docstrings to remove (following AGENT.md guidelines):

```
/backend/app/api/v1/auth.py
- 13 docstrings found (module + function/route level)
- Keep only if critical business logic not obvious from code

/backend/app/models/user.py
- Module docstring: "User model for database." (remove)
- Class docstring: "User model for authentication and project ownership." (remove)

/backend/app/services/*.py
- Remove all module and class docstrings
- Keep only function docstrings explaining non-obvious logic
```

### Frontend File Naming (Priority: MEDIUM)

All frontend files follow proper conventions:
- ✅ Components: PascalCase (PageBreadcrumbs.tsx, HelpTooltip.tsx)
- ✅ Hooks: camelCase (useBreadcrumbs.ts, usePasswordStrength.ts)
- ✅ Libraries: camelCase (apiClient.ts, helpTexts.ts)

No changes needed in frontend.

### Backend Variable Naming (Priority: MEDIUM)

Mixed conventions found in some files. Examples:
- Database columns: `dfx_identity_name` ✅ (correct snake_case)
- Service methods: `snake_case` ✅ (correct)
- Function parameters: Mostly `snake_case` ✅ (correct)

Status: Generally compliant, minor cleanup may be needed.

### Comments & Documentation (Priority: MEDIUM)

Audit findings:
- **Redundant comments**: Generally minimal
- **Missing explanations**: Some complex async logic could use brief comments
- **Docstrings**: Need systematic removal per AGENT.md

Example of redundant comment to remove:
```python
# Set user ID
user_id = 123
```

Example of good comment to keep:
```python
# Proactive refresh 5 minutes before expiry prevents logout
await apiClient.proactiveTokenRefresh()
```

## Refactoring Order

### Phase 1: Critical (Do First)
1. ✅ Create AGENT.md with standards ← DONE
2. Rename backend files (cleanDfx, domainManagement, etc.)
3. Update all import statements
4. Update main.py route registrations

### Phase 2: Important (Do Next)
1. Remove module-level docstrings
2. Remove class docstrings (if not explaining non-obvious inheritance)
3. Remove redundant function docstrings
4. Audit and clean variable naming

### Phase 3: Nice-to-Have
1. Add strategic comments for complex logic
2. Review function length (ensure < 30 lines)
3. Validate error handling patterns
4. Check for unused imports

## Files Needing Review

### Backend API Routes
- [ ] `/backend/app/api/v1/auth.py` (13 docstrings)
- [ ] `/backend/app/api/v1/projects.py`
- [ ] `/backend/app/api/v1/deployments.py`
- [ ] `/backend/app/api/v1/wallet.py`
- [ ] `/backend/app/api/v1/metrics.py`

### Backend Models
- [ ] `/backend/app/models/user.py` (2 docstrings)
- [ ] `/backend/app/models/project.py`
- [ ] `/backend/app/models/deployment.py`
- [ ] All other models for docstring cleanup

### Backend Services
- [ ] `/backend/app/services/auth.py`
- [ ] `/backend/app/services/projects.py`
- [ ] `/backend/app/services/password_reset.py`
- [ ] All other services for docstring cleanup

### Backend Schemas
- [ ] `/backend/app/schemas/user.py`
- [ ] `/backend/app/schemas/project.py`
- [ ] Review for redundant field documentation

### Frontend Components
- ✅ All compliant with naming standards
- Review for unnecessary comments

## Current Code Quality Metrics

### Compliance Summary
```
Backend Naming:
  - PascalCase Classes: ✅ 100%
  - snake_case Functions: ✅ 95% (minor inconsistencies)
  - snake_case Files: ⚠️ 60% (domainManagement, cleanDfx issues)
  
Frontend Naming:
  - PascalCase Components: ✅ 100%
  - camelCase Utilities: ✅ 100%
  - camelCase Functions: ✅ 95%
  
Docstrings:
  - Backend: ⚠️ Heavy docstring usage (needs cleanup)
  - Frontend: ✅ Minimal/none (good)
  
Comments:
  - Backend: ⚠️ Some redundant comments
  - Frontend: ✅ Clean, minimal comments
```

## Next Steps

1. **Immediate**: Don't build until standards are aligned
2. **Step 1**: Rename backend files with mixed casing
3. **Step 2**: Update imports after file renames
4. **Step 3**: Remove docstrings systematically
5. **Step 4**: Clean redundant comments
6. **Step 5**: Verify all tests still pass
7. **Step 6**: Run linters (pylint, eslint)

## Implementation Notes

### File Rename Strategy
```bash
# Backend API routes
mv backend/app/api/v1/cleanDfx.py backend/app/api/v1/clean_dfx.py
mv backend/app/api/v1/domainManagement.py backend/app/api/v1/domain_management.py
mv backend/app/api/v1/dynamicDeployment.py backend/app/api/v1/dynamic_deployment.py

# Backend models
mv backend/app/models/projectMetrics.py backend/app/models/project_metrics.py
```

### Update Imports
After renames, update all files importing these modules:
```python
# Before
from app.api.v1.cleanDfx import router

# After
from app.api.v1.clean_dfx import router
```

### Docstring Removal Strategy
Use find-and-replace per file to remove docstrings:
```python
# Remove these patterns:
1. """Module docstrings at file start"""
2. """Class docstrings"""
3. """Function docstrings for obvious methods"""
4. Keep: """Complex async logic that needs explanation"""
```

## Code Review Checklist

Before merging any PR:
- [ ] All files use correct naming convention (snake_case for files, camelCase/PascalCase for code)
- [ ] No module or class docstrings
- [ ] No redundant function docstrings
- [ ] Comments explain "why", not "what"
- [ ] All imports are used
- [ ] Functions are under 30 lines
- [ ] Error handling is present
- [ ] Tests pass
- [ ] No hardcoded secrets or API keys

## Resources

See `AGENT.md` for:
- Detailed naming conventions
- Code style guidelines
- File organization
- API design patterns
- DFX command reference
- Common patterns and prohibited patterns
