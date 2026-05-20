# Family Calendar Monorepo

This repository is organized as a monorepo with separate backend and frontend apps.

## Project Structure

```text
family_calendar_api/
├── backend/                # FastAPI backend app, tests, and backend deployment configs
├── frontend/               # React + Vite frontend app
├── docker-compose.yml      # Local full-stack orchestration (API + DB + optional tests)
├── PRODUCTION_CHECKLIST.md # Deployment hardening checklist
├── mypy.ini                # Python static type checker config
└── backup.sql              # Database backup artifact
```

## Architecture Overview

The platform is split into two deployable applications and one managed database:

- **Frontend (Vercel)**: Serves the React SPA, handles client-side routing, and calls backend APIs over HTTPS.
- **Backend (Render)**: Runs FastAPI (`app.main:app`) for authentication, family/event business logic, and data access.
- **Neon PostgreSQL**: Managed Postgres instance used by the backend via `DATABASE_URL`.

### Runtime interaction model

1. Browser loads frontend from Vercel.
2. Frontend sends authenticated API requests (JWT Bearer token) to backend on Render.
3. Backend validates auth/permissions, executes service logic, and reads/writes Neon PostgreSQL.
4. Backend returns JSON responses to frontend.

### Request Flow Diagram

```text
[User Browser]
      |
      v
[Vercel Frontend (React/Vite)]
      | HTTPS JSON API (Bearer JWT)
      v
[Render Backend (FastAPI)]
      | SQLAlchemy / psycopg
      v
[Neon PostgreSQL]
```

### Deployment flow

- **Backend deploy**: Render builds from `backend/`, installs `backend/requirements.txt`, starts `app.main:app` via Gunicorn/Uvicorn worker.
- **Frontend deploy**: Vercel builds from `frontend/`, injects API base URL env vars, and serves static assets at edge.
- **Cross-service config**: Backend `ALLOWED_ORIGINS` must include Vercel domain(s); frontend must point to Render API base URL.

## Quick start
### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Full stack with Docker
```bash
docker compose up --build
```


## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
