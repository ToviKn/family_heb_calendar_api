# Family Calendar Backend

Production-oriented FastAPI backend.

## Project Structure

```text
backend/
├── app/
│   ├── main.py             # FastAPI app factory/entrypoint (`app.main:app`)
│   ├── config.py           # Centralized runtime settings/env parsing
│   ├── exceptions.py       # Domain and API exception hierarchy
│   ├── logging_config.py   # Structured logging and request-id helpers
│   ├── routes/             # HTTP layer: request/response contracts and endpoint wiring
│   ├── services/           # Business logic layer used by route handlers
│   ├── models/             # SQLAlchemy entities + Pydantic schema models
│   ├── storage/            # DB engine/session setup and schema migration helpers
│   └── utils/              # Shared pure utility helpers
├── tests/                  # Pytest suite (unit + API/integration coverage)
├── requirements.txt        # Backend Python dependencies
├── Dockerfile              # Production image build for Render/container runtimes
├── Dockerfile.test         # Test image build for CI/containerized test runs
├── render.yaml             # Render service blueprint (build/start/env)
├── pytest.ini              # Pytest discovery/config
└── .env.example            # Environment variable template
```

### Directory responsibilities

- **`app/routes`**: Endpoint modules that map HTTP routes to service calls and dependency injection.
- **`app/services`**: Core domain behavior (auth, families, events, notifications, date conversion).
- **`app/models`**: ORM tables and API payload models.
- **`app/storage`**: Database connectivity, session lifecycle, enums, and safe schema migration helpers.
- **`app/utils`**: Reusable utility functions with minimal side effects.
- **`tests`**: End-to-end API tests plus service/unit-level regressions.
- **`Dockerfile`**: Backend production runtime image.
- **`render.yaml`**: Render deploy configuration aligned with `app.main:app`.

## Environment variables
Copy `.env.example` and configure:
- `DATABASE_URL` (required)
  - **Local Docker Compose**: use `@db:5432` (service name `db` from `docker-compose.yml`) so the backend container reaches Postgres over the Docker network.
  - **Production (optional)**: swap to a hosted URL (for example Neon) and keep SSL options such as `sslmode=require`.
- `JWT_SECRET_KEY` (required)
- `ALLOWED_ORIGINS` (required in production)
- optional: `ENV`, `ENABLE_API_DOCS`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DEBUG`, pool/log settings

## Local setup
#### Linux/macOS
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

#### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run
#### Linux/macOS
## Run
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Windows PowerShell
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Test
#### Linux/macOS
## Test
```bash
pytest -v
```

#### Windows PowerShell
```powershell
pytest -v
```

## Docker
```bash
docker build -t family-calendar-api .
docker run --env-file .env -p 8000:8000 family-calendar-api
```

## Deploy
- Render start command: `gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:$PORT app.main:app`.
- Vercel-compatible frontend should call this backend URL through env config.


## Local Docker Compose workflow
Use the monorepo root `docker-compose.yml` for local full-stack development:

```bash
docker compose up --build
```

### Why `db` is used in `DATABASE_URL`
Inside Docker Compose, services communicate over an internal network by **service name**.  
That is why the backend uses `postgresql+psycopg://...@db:5432/...` instead of `localhost`.

### Swagger/OpenAPI in local dev
Local `.env` sets `ENABLE_API_DOCS=true`, so these endpoints are available:
- `/docs`
- `/redoc`
- `/openapi.json`

### Migrations in local dev
This project runs legacy startup migrations when `RUN_LEGACY_STARTUP_MIGRATIONS=true` (set in local `.env.example`).
If you need to re-run from a clean local database:

```bash
docker compose down -v
docker compose up --build
```

`docker compose down -v` removes the Postgres volume and resets local DB data.
