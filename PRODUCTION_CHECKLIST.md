# Production Readiness Checklist

## Backend (Render)
- Set `ENV=production`.
- Set `ENABLE_API_DOCS=false` unless you intentionally expose docs.
- Set a strong `JWT_SECRET_KEY` (32+ random bytes).
- Set `ALLOWED_ORIGINS=https://<your-vercel-domain>`.
- Set `DATABASE_URL` to the Neon pooled connection string.
- Optional tuning:
  - `WEB_CONCURRENCY=2`
  - `GUNICORN_TIMEOUT=60`
  - `GUNICORN_GRACEFUL_TIMEOUT=30`

## Frontend (Vercel)
- Set `VITE_API_BASE_URL=https://<your-render-domain>`.
- Ensure login route is publicly accessible and protected routes require auth.

## Neon PostgreSQL
- Use SSL-enabled URL provided by Neon.
- Run Alembic migrations during deploy before serving traffic.
- Verify database role has least privilege required by app.

## Security hardening still recommended
- Add request rate limiting (e.g., `slowapi`) for `/auth/login`.
- Add structured auth audit logs for login failures.
- Add refresh token rotation (access token currently single JWT only).
- Add centralized monitoring/alerts (Sentry/Datadog/OpenTelemetry).
