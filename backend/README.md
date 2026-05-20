# Family Calendar Backend

Production-oriented FastAPI backend.

## App layout
- `app/main.py`: FastAPI entrypoint (`app.main:app`).
- `app/config.py`: centralized Settings (env vars).
- `app/routes/`, `app/services/`, `app/models/`, `app/storage/`, `app/utils/`.
- `tests/`: pytest suite.

## Environment variables
Copy `.env.example` and configure:
- `DATABASE_URL` (required)
- `JWT_SECRET_KEY` (required)
- `ALLOWED_ORIGINS` (required in production)
- optional: `ENV`, `ENABLE_API_DOCS`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DEBUG`, pool/log settings

## Run
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Test
```bash
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
