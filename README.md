# Canistra ICP Hosting

Host static sites (HTML, CSS, JavaScript) on the **Internet Computer** from a web dashboard. Users sign up, edit projects in the browser, fund a custodial ICP wallet, convert ICP to cycles, and publish to asset canisters on IC mainnet (or a local dfx replica for development).

**Stack:** Next.js frontend · FastAPI backend · PostgreSQL · dfx · Celery/Redis (optional, for background deploys)

---

## How it works

Follow these steps to go from zero to a live site on ICP.

### Step 1 — Install and start the stack

1. Complete [First-time setup](#first-time-setup) below (database, backend, frontend).
2. From the repo root, run:

```bash
chmod +x start.sh
./start.sh
```

3. Open the dashboard at **http://localhost:3000** and sign in.

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

For local canister deploys, use `./start.sh --local-dfx` and set `DEPLOY_NETWORK=local` in `backend/.env`.

### Step 2 — Fund your wallet

1. Open **Wallet** in the sidebar.
2. Copy your **Deposit address (Account ID)** or scan the QR code.
3. For testnet development, get **TESTICP** from [faucet.internetcomputer.org](https://faucet.internetcomputer.org) (TESTICP tab).
4. Click **Check deposits**, then convert ICP/TESTICP to **cycles** when ready to deploy.

![Wallet — deposit address, QR code, and balance](docs/assets/progress/screenshot-1.png)

### Step 3 — Check the dashboard

After funding, the dashboard shows your project count, live deployments, and cycle balance. Create a project with **New project** or open an existing one from **Recent projects**.

![Dashboard — projects overview and cycle balance](docs/assets/progress/screenshot-2.png)

### Step 4 — Edit and publish to ICP

1. Open a project in the **Project editor**.
2. Edit `index.html`, `style.css`, and `script.js` in the browser (or upload a folder).
3. Click **Save & Publish** to push files to your asset canister.
4. Use **Visit site** to open the live `.icp0.io` URL.

![Project editor — in-browser code editor and live ICP URL](docs/assets/progress/screenshot-3.png)

**Production:** set `DEPLOY_NETWORK=ic` and `USE_TESTICP=false` in `backend/.env`, fund with real ICP, then follow the same wallet → publish flow. See [docs/deployment/PRODUCTION_CHECKLIST.md](docs/deployment/PRODUCTION_CHECKLIST.md).

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

Press **Ctrl+C** to stop backend and frontend.

> **Tip:** See [How it works](#how-it-works) above for the full wallet → dashboard → publish walkthrough with screenshots.

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

See [docs/deployment/PRODUCTION_CHECKLIST.md](docs/deployment/PRODUCTION_CHECKLIST.md) before going live.

---

## Project layout

```
├── frontend/          Next.js dashboard (wallet, projects, editor, deploy)
├── backend/           FastAPI API + dfx integration
├── start.sh           Start backend + frontend together
├── testing/           API scenario checks & unit tests
└── docs/              Organized docs (deployment, architecture, reports, …)
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
