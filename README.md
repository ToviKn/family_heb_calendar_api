# Family Calendar API

A production-oriented FastAPI backend for managing family events across Gregorian and Hebrew calendars. The API provides JWT-based authentication, family-scoped event management, notifications, and date conversion utilities.

## Features

- JWT authentication and protected endpoints.
- Family management and membership support.
- Event CRUD with Gregorian/Hebrew date handling.
- Date conversion endpoints (`/convert/hebrew`, `/convert/gregorian`).
- Notification creation and listing.
- Structured JSON logging with request correlation IDs.
- OpenAPI documentation via `/docs` and `/redoc`.

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn/Gunicorn
- SQLAlchemy 2.x
- PostgreSQL (production), SQLite (tests)
- Passlib + python-jose for authentication
- Docker + Render deployment support

## Project Structure

```text
.
├── main.py                  # FastAPI entry point and middleware
├── models/                  # ORM and API schema models
│   ├── models.py               # SQLAlchemy ORM models
│   ├── user.py                 # User API schema types
│   ├── event.py                # Event/date conversion API schema types
│   └── notification.py         # Notification API schema types 
├── routes/                  # API route modules
│   ├── auth.py                 # Login endpoint
│   ├── users.py                # User creation endpoint
│   ├── events.py               # Event CRUD and search endpoints
│   ├── families.py             # Family + membership endpoints
│   ├── notifications.py        # Notification endpoints and reminder trigger
│   ├── convert.py              # Date conversion endpoints
├── services/                # Business logic layer
│   ├── auth_service.py         # Password hashing, JWT, current-user resolution
│   ├── user_service.py         # User creation logic
│   ├── family_service.py       # Family + membership creation logic
│   ├── event_service.py        # Event rules, queries, and mutation logic
│   ├── date_service.py         # Date validation/conversion/recurrence calculations
│   └── notification_service.py # Notification and reminder workflows
├── storage/                 # Database/session/migration helpers
│   ├── database.py             # Engine/session configuration and DB session dependency
│   ├── enums.py                # Shared enum values
│   └── schema_migrations.py    # Runtime-safe schema migration helpers
├── tests/                   # Automated tests
├── logging_config.py        # Structured logging config
├── exceptions.py            # Domain/API exception types
├── requirements.txt         # Runtime dependencies
├── Dockerfile               # Production container image
├── Dockerfile.test          # Test container image
├── docker-compose.yml       # Local development/test orchestration
├── render.yaml              # Render blueprint
└── .env.example             # Environment variable template
```

## Environment Variables

Copy `.env.example` and set secure values before running in production.

Required:

- `DATABASE_URL`: SQLAlchemy database URL.
  - Example (Render/Postgres): `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB_NAME`
- `JWT_SECRET_KEY`: Strong random secret for signing access tokens.
- `ALLOWED_ORIGINS`: Comma-separated frontend origins for CORS.

Optional:

- `ACCESS_TOKEN_EXPIRE_MINUTES` (default: `60`)
- `DEBUG` (default: `false`)
- `LOG_LEVEL` (default: `INFO`)
- `SQL_LOG_LEVEL` (default: `WARNING`)
- `ENV` (default: `production`)

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Start locally:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 main:app
```

Docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Setup

Build and run API + Postgres locally:

```bash
docker compose up --build
```

Run tests profile:

```bash
docker compose --profile test run --rm tests
```

## Render Deployment

This repository includes `render.yaml` for service provisioning.

1. Push this repository to GitHub.
2. In Render, create a **Blueprint** from the repo.
3. Set `DATABASE_URL`, `JWT_SECRET_KEY`, and `ALLOWED_ORIGINS` as environment variables.
4. Deploy and verify `/health` and `/docs`.

Start command used in production:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:$PORT main:app
```

## API Usage

### Authentication

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=StrongPass123"
```

Use the returned token:

```bash
-H "Authorization: Bearer <access_token>"
```

### Documentation

- `GET /docs` for interactive Swagger UI.
- `GET /openapi.json` for raw OpenAPI schema.

## 🌐 Live API

Base URL:
https://family-heb-calendar-api.onrender.com

API Documentation (Swagger):
https://family-heb-calendar-api.onrender.com/docs

Health Check:
https://family-heb-calendar-api.onrender.com/health


## Production Notes

- Do not commit `.env` files or secrets.
- Restrict `ALLOWED_ORIGINS` to trusted frontend domains.
- Keep `DEBUG=false` in production.
- Use managed PostgreSQL for production workloads.
