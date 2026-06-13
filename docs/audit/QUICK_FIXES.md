# Frontend Audit - Quick Fixes Guide

## Fix #1: Build Error in fileUploader.tsx (CRITICAL - 2 MINUTES)

**File:** `/src/components/ui/fileUploader.tsx`
**Line:** 77

### Current Code (WRONG):
```tsx
const getFileIcon = (file: FileWithPreview) => {
  if (file.type.startsWith('image/')) return <Image className="h-4 w-4" alt="Image file" />;
  if (file.type.startsWith('video/')) return <Film className="h-4 w-4" />;
  // ...
}
```

### Fixed Code:
```tsx
const getFileIcon = (file: FileWithPreview) => {
  if (file.type.startsWith('image/')) return <Image className="h-4 w-4" />;
  if (file.type.startsWith('video/')) return <Film className="h-4 w-4" />;
  // ...
}
```

**Change:** Remove `alt="Image file"` prop from `<Image>` icon component
**Why:** `Image` is a lucide icon, not an HTML element. It doesn't accept `alt` prop.
**Impact:** Unblocks build process immediately

---

## Fix #2: Security Risk - Add .env to .gitignore (CRITICAL - 1 MINUTE)

**File:** `/frontend/.gitignore`

### Add These Lines:
```
# Environment variables - should NEVER be committed
.env
.env.local
.env.*.local
.env.production
```

### Then Run:
```bash
git rm --cached .env
git commit -m "Remove .env from tracking (security)"
```

**Why:** Environment files contain sensitive configuration and should never be committed
**Impact:** Prevents accidental commit of secrets in future

---

## Fix #3: Remove Unused SWR Dependency (IMPORTANT - 5 MINUTES)

**File:** `/frontend/package.json`

### Current (Lines 45):
```json
{
  "dependencies": {
    // ... other deps
    "swr": "^2.4.1",
    // ... other deps
  }
}
```

### After Fix:
```json
{
  "dependencies": {
    // ... other deps
    // swr removed - using React Query instead
    // ... other deps
  }
}
```

### Commands:
```bash
cd frontend
npm uninstall swr
npm install
```

**Why:** SWR is unused (no imports in codebase). React Query already handles data fetching.
**Impact:** Reduces bundle size by ~35KB

---

## Fix #4: Type Safety - Add Types to apiClient Methods (HIGH - 30 MINUTES)

**File:** `/src/lib/apiClient.ts`

### Issue: Multiple methods return `Promise<any>`

### Step 1: Update Types File First

**File:** `/src/types/api.ts` - Add these interfaces:

```typescript
// Add after existing types

export interface DeploymentStatus {
  deployment_id: number;
  status: string;
  message: string;
  created_at: string;
  updated_at?: string;
}

export interface ProjectDeployment extends DeploymentStatus {
  project_id: number;
}

export interface DashboardCanister {
  id: string;
  name: string;
  status: string;
  cycles_balance?: string;
  created_at: string;
}

export interface DashboardActivity {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  status: 'success' | 'failed' | 'pending';
}

export interface ProjectMetrics {
  timestamp: string;
  cycles_balance: string;
  memory_usage?: string;
  request_count?: number;
}

export interface DashboardOverview {
  projects: {
    total: number;
    active: number;
    deployed: number;
  };
  aggregated_metrics: {
    total_cycles_balance: string;
    total_memory_usage?: string;
  };
  recent_projects: Project[];
}

export interface CronStatus {
  status: string;
  last_run?: string;
  next_run?: string;
}

export interface NetworkStatus {
  status: string;
  node_count?: number;
  subnet_count?: number;
}
```

### Step 2: Update apiClient.ts

```typescript
// BEFORE
async getDeploymentStatus(projectId: string, deploymentId: string): Promise<any> {
  const response = await this.client.get(`/deployments/projects/${projectId}/deployments/${deploymentId}`);
  return response.data;
}

// AFTER
async getDeploymentStatus(projectId: string, deploymentId: string): Promise<DeploymentStatus> {
  const response = await this.client.get<DeploymentStatus>(`/deployments/projects/${projectId}/deployments/${deploymentId}`);
  return response.data;
}
```

### Apply to All These Methods:

```typescript
// Change these methods:
async getProjectDeployments(...): Promise<ProjectDeployment[]>
async getNetworkStatus(): Promise<NetworkStatus>
async getCronStatus(): Promise<CronStatus>
async triggerManualConversion(...): Promise<any>  // -> Promise<{ success: boolean; message: string }>
async getDashboardCanisters(): Promise<DashboardCanister[]>
async getDashboardActivities(): Promise<DashboardActivity[]>
async getProjectMetrics(projectId: string): Promise<ProjectMetrics[]>
async getProjectLiveMetrics(projectId: string): Promise<ProjectMetrics[]>
async getDashboardOverview(): Promise<DashboardOverview>
async updateCanister(...): Promise<DeploymentStatus>
async deleteCanister(...): Promise<{ success: boolean; message: string }>
```

**Time:** ~30 minutes
**Impact:** Significant improvement in type safety and IDE autocomplete

---

## Fix #5: Type Safety in Dashboard Page (HIGH - 10 MINUTES)

**File:** `/src/app/dashboard/page.tsx`
**Lines:** 47-111

### Current Code (WRONG):
```tsx
const columns = [
  {
    key: 'name' as const,
    label: 'Name',
    render: (project: any) => ( // WRONG - any type
      // ...
    )
  }
]
```

### Fixed Code:
```tsx
interface ProjectRenderProps {
  id: number;
  name: string;
  status: string;
  canister_id?: string;
  cycles_balance?: string;
  created_at: string;
  url?: string;
}

const columns = [
  {
    key: 'name' as const,
    label: 'Name',
    render: (project: ProjectRenderProps) => ( // PROPER TYPE
      <div>
        <div className="font-medium">{project.name}</div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>ID: {project.id}</span>
          {project.canister_id && (
            <>
              <span>•</span>
              <span>{project.canister_id.slice(0, 8)}...</span>
              <CopyButton value={project.canister_id} />
            </>
          )}
        </div>
      </div>
    ),
  },
  // ... other columns
]
```

**Time:** ~10 minutes
**Impact:** Better type checking and IDE support

---

## Fix #6: Replace window.location.href with useRouter (MEDIUM - 5 MINUTES)

**File 1:** `/src/app/dashboard/projects/page.tsx`

### Current (WRONG):
```tsx
onClick={() => window.location.href = `/dashboard/projects/${project.id}`}
```

### Fixed:
```tsx
const router = useRouter();

onClick={() => router.push(`/dashboard/projects/${project.id}`)}
```

### File 2: `/src/app/canisters/[id]/page.tsx`

### Current (WRONG):
```tsx
window.location.href = '/canisters'
```

### Fixed:
```tsx
const router = useRouter();
router.push('/canisters')
```

**Why:** Full page reloads are slower than Next.js client-side navigation
**Impact:** Better UX and performance

---

## Summary of Fixes

| Fix | File | Time | Priority | Impact |
|-----|------|------|----------|--------|
| 1 | fileUploader.tsx | 2 min | CRITICAL | Unblocks build |
| 2 | .gitignore | 1 min | CRITICAL | Security |
| 3 | package.json | 5 min | HIGH | Bundle size |
| 4 | apiClient.ts | 30 min | HIGH | Type safety |
| 5 | dashboard/page.tsx | 10 min | HIGH | Type safety |
| 6 | Multiple | 5 min | MEDIUM | Performance |

**Total Time:** ~50 minutes
**Total Impact:** Resolves all critical and most high-priority issues

---

## Verification Steps

After applying fixes, run:

```bash
cd frontend

# Check build
npm run build

# Check types
npx tsc --noEmit

# Check lint
npm run lint

# Check dependencies
npm list swr  # Should show "npm ERR!" after removal
```

All should pass without errors.

---

## Testing Checklist

After fixes:

- [ ] Build completes without errors
- [ ] Login/logout flows work
- [ ] Token refresh works
- [ ] Navigate between pages smoothly
- [ ] Dashboard loads without errors
- [ ] File upload component works
- [ ] API calls return proper data
- [ ] Type checking passes

