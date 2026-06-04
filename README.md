# Family Calendar Monorepo

This repository is organized as a monorepo with separate backend and frontend applications.

## Project Structure

```text
family_calendar_api/
├── backend/                # FastAPI backend app, tests, and deployment configs
├── frontend/               # React + Vite frontend app
├── docker-compose.yml      # Local full-stack orchestration
├── PRODUCTION_CHECKLIST.md # Deployment hardening checklist
├── mypy.ini                # Python static type checker config
└── backup.sql              # Database backup artifact
```

## Architecture Overview

The platform consists of:

* **Frontend (Vercel)** – React SPA served globally.
* **Backend (Render)** – FastAPI application (`app.main:app`).
* **Neon PostgreSQL** – Managed PostgreSQL database.

### Runtime Interaction Model

1. Browser loads the frontend from Vercel.
2. Frontend sends authenticated API requests (JWT Bearer token) to the backend.
3. Backend validates permissions, executes business logic, and accesses PostgreSQL.
4. Backend returns JSON responses.

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

## Deployment

### Backend (Render)

* Builds from `backend/`
* Installs dependencies from `backend/requirements.txt`
* Runs `app.main:app` via Gunicorn/Uvicorn workers

### Frontend (Vercel)

* Builds from `frontend/`
* Injects environment variables during build
* Serves static assets globally

### Cross-Service Configuration

* Backend `ALLOWED_ORIGINS` must include frontend domains.
* Frontend API URL must point to the deployed backend.

## Quick Start

### Backend

#### Linux/macOS

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

#### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

### Frontend

#### Linux/macOS

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

#### Windows PowerShell

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

### Full Stack with Docker

```bash
docker compose up --build
```

## CI

A GitHub Actions pipeline runs on every `push` and `pull_request`.

### Backend Job

* Installs Python dependencies
* Runs `pytest`

### Frontend Job

* Installs Node dependencies
* Builds the production bundle

The workflow fails automatically if tests or builds fail.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
