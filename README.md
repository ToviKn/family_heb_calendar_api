# Family Calendar Monorepo

This repository is organized as a monorepo with separate backend and frontend applications.

## Project Structure

```text
family_calendar_api/
├── backend/                # FastAPI backend app, tests, and deployment configs
├── frontend/               # React + Vite frontend app
├── docker-compose.yml      # Local full-stack orchestration
├── PRODUCTION_CHECKLIST.md # Deployment hardening checklist
└── mypy.ini                # Python static type checker config
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

## Third-Party Libraries

This project depends on several open-source libraries, including FastAPI, SQLAlchemy, Pydantic, Uvicorn, Convertdate, HTTPX, Passlib, and PostgreSQL drivers.

All third-party libraries remain the property of their respective authors and are distributed under their own licenses. See `requirements.txt` and the respective project repositories for license details.

## Acknowledgements

Hebrew calendar calculations are based on the open-source `convertdate` library.


## Notification delivery

The `notifications` table remains the source of truth for all in-app notifications. Every application flow that creates a `Notification` sends the committed notification through the notification dispatcher, including event reminders, family invitations, join requests, join request approvals/rejections, and event create/update/delete notifications.

The dispatcher is the single delivery pipeline. It resolves a notification template for the notification type or `metadata.notification_kind`, then attempts each enabled channel independently: email and browser push. Templates define the email subject, HTML body, plain-text body, push title, and push body so new notification types can be added by registering templates without changing dispatcher control flow. One channel failing is logged and does not prevent the other channel from running.

### Email configuration

Email delivery uses SMTP only and reads all configuration from environment variables:

- `EMAIL_PROVIDER=smtp`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`

Emails include both HTML content and a plain-text fallback.

### Browser push configuration

Backend VAPID variables:

- `VAPID_PRIVATE_KEY`
- `VAPID_PUBLIC_KEY`
- `VAPID_EMAIL`

Frontend Vite variable:

- `VITE_VAPID_PUBLIC_KEY`

Authenticated clients store browser subscriptions with `POST /api/push/subscribe` and remove them with `DELETE /api/push/unsubscribe`. Expired push subscriptions are deleted automatically after a 404 or 410 response from the push provider.

### User notification preferences

Authenticated users can manage delivery preferences at Settings → Notifications. Preferences include email delivery, push delivery, reminders for events occurring today, and reminders one day before an event.

### Enabling browser notifications

Open Settings → Notifications and choose **Enable** in the browser notification prompt. If permission is granted, the app registers `service-worker.js`, creates a push subscription, and sends that subscription to the API.
