# Family Calendar Monorepo

This repository is organized as a monorepo with separate backend and frontend apps.

## Structure
- `backend/`: FastAPI API service (app code, tests, Docker/Render config).
- `frontend/`: Vite/React frontend.
- `docker-compose.yml`: local multi-service orchestration.

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
