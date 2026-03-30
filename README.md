# Family Calendar API

Family Calendar API is a FastAPI backend for managing family events 
with support for **Gregorian** and **Hebrew** calendars, 
recurring events, JWT authentication, and notifications.

## Project Overview

This service provides:
- User registration and authentication (`/users`, `/auth/login`)
- Family and membership management (`/families`)
- Event CRUD with recurrence + Hebrew/Gregorian support (`/events`)
- Date conversion endpoints (`/convert/*`)
- Notification and reminder processing (`/notifications`)

The API uses SQLAlchemy for persistence and a centralized structured logging configuration for operational observability.

## Setup Instructions

### 1) Local installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Environment variables

Required:

```bash
export DATABASE_URL="postgresql+psycopg://<user>:<password>@<host>:5432/<db>"
export JWT_SECRET_KEY="<strong-random-secret>"
export ALLOWED_ORIGINS="https://your-frontend.example.com"
```

Optional:

```bash
export DEBUG="false"
export LOG_LEVEL="INFO"
export SQL_LOG_LEVEL="WARNING"
export ENABLE_DEBUG_ROUTES="false"
export ACCESS_TOKEN_EXPIRE_MINUTES="60"
```

### 3) Run the app

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 main:app
```

Docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4) Docker

Build and run:

```bash
docker compose up --build
```

Run tests in Docker:

```bash
docker compose --profile test run --rm tests
```

## API Usage

## Authentication

1. Create a user:

```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"User","password":"StrongPass123"}'
```

2. Login to get JWT token:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=StrongPass123"
```

3. Use token for protected endpoints:

```bash
-H "Authorization: Bearer <access_token>"
```

## Main endpoints

- `POST /events/` create event
- `GET /events/` search events by `year/month/day`
- `GET /events/today` today’s events
- `GET /events/upcoming?days=30` upcoming events
- `GET /events/family/{family_id}` family events
- `GET /convert/hebrew` Gregorian -> Hebrew conversion
- `GET /convert/gregorian` Hebrew -> Gregorian conversion
- `POST /notifications/` create notification
- `GET /notifications/` list user notifications

## Logging

The project uses the existing centralized logger in `logging_config.py` and emits **structured JSON logs**.

### Log levels
- `INFO`: normal operations (request completed, entity created, commits)
- `WARNING`: expected issues (invalid login, missing resource, rollback)
- `ERROR`: unexpected failures (exceptions, DB failures)

### Logging behavior
- Request correlation via `request_id` (from `X-Request-ID` or generated)
- Context fields included where available (`operation`, `user_id`, `event_id`, `family_id`, etc.)
- Sensitive fields are redacted (passwords/tokens/API keys)
- API middleware logs request completion/failure with duration and status
- Routes and services log operation start/completion/failures
- Database layer logs session open/close, commits, and rollbacks

## Project Structure

```text
family_calendar_api/
├── .env.example                # Example deployment environment variables
├── .gitignore                  # Git ignore rules for local/runtime artifacts
├── render.yaml                 # Render service blueprint
├── main.py                     # FastAPI entry point, middleware, app wiring
├── routes/                     # API endpoint modules (auth, users, events, etc.)
│   ├── auth.py                 # Login endpoint
│   ├── users.py                # User creation endpoint
│   ├── events.py               # Event CRUD and search endpoints
│   ├── families.py             # Family + membership endpoints
│   ├── notifications.py        # Notification endpoints and reminder trigger
│   ├── convert.py              # Date conversion endpoints
│   └── debug.py                # Debug database inspection endpoint
├── services/                   # Business logic and orchestration
│   ├── auth_service.py         # Password hashing, JWT, current-user resolution
│   ├── user_service.py         # User creation logic
│   ├── event_service.py        # Event rules, queries, and mutation logic
│   ├── date_service.py         # Date validation/conversion/recurrence calculations
│   └── notification_service.py # Notification and reminder workflows
├── models/                     # SQLAlchemy + Pydantic models/schemas
│   ├── models.py               # SQLAlchemy ORM models
│   ├── user.py                 # User API schema types
│   ├── event.py                # Event/date conversion API schema types
│   └── notification.py         # Notification API schema types
├── storage/                    # Database configuration and schema support
│   ├── database.py             # Engine/session configuration and DB session dependency
│   ├── enums.py                # Shared enum values
│   └── schema_migrations.py    # Runtime-safe schema migration helpers
├── tests/                      # Unit/integration test suite
├── logging_config.py           # Structured logging config + request_id + redaction
├── exceptions.py               # Custom API and domain exceptions
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Production image build
├── Dockerfile.test             # Test image build
├── docker-compose.yml          # Multi-service local orchestration
├── README.md                   # Project documentation
```

## Code Quality

- Keep business logic in `services/`.
- Keep route handlers focused on request/response orchestration.
- Preserve existing API contracts.
- Run tests before shipping changes.

## Testing

```bash
pytest
```
