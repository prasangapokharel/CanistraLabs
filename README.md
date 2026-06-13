# Canistra ICP Hosting

Host static sites (HTML, CSS, JavaScript) on the **Internet Computer** from a web dashboard. Users sign up, edit projects in the browser, fund a custodial ICP wallet, convert ICP to cycles, and publish to asset canisters on IC mainnet (or a local dfx replica for development).

**Stack:** Next.js frontend · FastAPI backend · PostgreSQL · dfx · Celery/Redis (optional, for background deploys)

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| **Node.js 20+** | Frontend |
| **Python 3.12+** | Backend |
| **PostgreSQL** | User/project data |
| **dfx** | Deploy & manage canisters |
| **Redis** (optional) | Background deploy queue |

---

## First-time setup

### 1. Database

Create a PostgreSQL database and user (example):

```bash
sudo -u postgres psql -c "CREATE USER icp WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE icp OWNER icp;"
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# Edit .env — set DATABASE_URL, JWT_SECRET_KEY, ENCRYPTION_KEY, ADMIN_API_KEY

# Run migrations
alembic upgrade head
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. ICP / dfx (optional for local deploys)

```bash
dfx --version   # needs dfx 0.20+
```

For **mainnet** deploys (default in `.env.example`): fund your wallet with real ICP and convert to cycles in the app.

For **local** deploys: set `DEPLOY_NETWORK=local` in `backend/.env` and use `./start.sh --local-dfx`.

---

## Start everything

From the repo root:

```bash
chmod +x start.sh
./start.sh
```

With local dfx replica (local canister deploys):

```bash
./start.sh --local-dfx
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

Press **Ctrl+C** to stop backend and frontend.

---

## Start separately

**Backend only**

```bash
cd backend
source .venv/bin/activate
python run.py
```

**Frontend only** (proxies `/api/v1/*` to the backend)

```bash
cd frontend
npm run dev
```

**Production frontend build**

```bash
cd frontend
npm run build
npm start
```

**Celery worker** (optional — async deploys; falls back to sync if Redis is down)

```bash
cd backend
source .venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

---

## Environment

Copy `backend/.env.example` → `backend/.env`. Important variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `DEPLOY_NETWORK` | `ic` (mainnet) or `local` (dfx replica) |
| `USE_TESTICP` | `false` for real ICP (production) |
| `JWT_SECRET_KEY` | Auth signing key (32+ chars) |
| `ENCRYPTION_KEY` | Custodial identity encryption (32+ chars) |

See [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) before going live.

---

## Project layout

```
├── frontend/          Next.js dashboard (wallet, projects, editor, deploy)
├── backend/           FastAPI API + dfx integration
├── start.sh           Start backend + frontend together
├── testing/           API scenario checks & unit tests
└── docs/              Deployment & architecture notes
```

---

## Quick test

```bash
cd backend && source .venv/bin/activate
python ../testing/backend_scenario_check.py
```

---

## License

See repository license file if present.
