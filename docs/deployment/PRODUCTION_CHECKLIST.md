# Production checklist — Canistra ICP Hosting

## Environment (`backend/.env`)

| Variable | Production value |
|----------|------------------|
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `ENCRYPTION_KEY` | Required (32+ chars, separate from JWT) |
| `JWT_SECRET_KEY` | Strong random (32+ chars) |
| `ADMIN_API_KEY` | Strong random (32+ chars) |
| `CORS_ORIGINS` | Your real frontend URL(s) only |
| `USE_TESTICP` | `false` |
| `DEPLOY_NETWORK` | `ic` |
| `DFX_NETWORK` | `ic` |
| `FRONTEND_URL` / `BACKEND_URL` | Public HTTPS URLs |

## Services to run

1. **PostgreSQL** — `DATABASE_URL`
2. **Backend** — `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. **Frontend** — `cd frontend && npm run build && npm start`
4. **Redis + Celery worker** (optional async deploy) — `celery -A app.tasks.celery_app worker`

## Pre-deploy verification

```bash
# Frontend production build
cd frontend && npm run build

# Backend health
curl -s http://localhost:8000/health

# Backend imports
cd backend && source .venv/bin/activate && python -c "from app.main import create_app; create_app()"
```

## User flows (manual smoke test)

- [ ] Sign up / login / logout
- [ ] Create project → edit → deploy
- [ ] Wallet: deposit address, convert cycles
- [ ] Visit live URL
- [ ] Metrics page (ICP canister status)
- [ ] Project on/off toggle (stop/start canister)
- [ ] Delete project

## Not production-ready yet (skip or disable)

- Custom domains UI (API exists, UI not wired)
- Email verification UI (optional; set `REQUIRE_EMAIL_VERIFICATION=false` unless implemented)
- `/dashboard/notifications`, `/help` links (placeholder routes)
