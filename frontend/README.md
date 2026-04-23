# Frontend (React + TypeScript + Vite)

This folder contains the frontend scaffold for the Family Hebrew Calendar app.

## Stack

- React + TypeScript
- Vite
- React Router
- Axios
- Tailwind CSS

## Folder structure

```text
frontend/
├── src/
│   ├── app/            # App root component
│   ├── layouts/        # Shared route layouts
│   ├── lib/api/        # Axios client and typed API clients
│   ├── pages/          # Route-level pages
│   ├── router/         # React Router definitions
│   └── styles/         # Global styles (Tailwind entrypoint)
├── .env.example
├── .npmrc
├── index.html
├── package.json
├── postcss.config.cjs
├── tailwind.config.ts
├── tsconfig*.json
└── vite.config.ts
```

## Run locally

### 1) Start backend API

From repo root (example):

```bash
cp .env.example .env
# set DATABASE_URL, JWT_SECRET_KEY, ALLOWED_ORIGINS in .env
pip install -r requirements.txt
gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 main:app
```

### 2) Start frontend

In a second terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open: <http://localhost:5173>

## Build + preview

```bash
npm run build
npm run preview
```

## Type-check

```bash
npm run typecheck
```

## npm 403 troubleshooting

If `npm install` fails with HTTP 403, run:

```bash
npm config set registry https://registry.npmjs.org/
npm config delete _auth
npm config delete _authToken
npm config delete proxy
npm config delete https-proxy
npm cache clean --force
```

Then retry:

```bash
npm install
```

Additional checks:

- Confirm `frontend/.npmrc` points to `https://registry.npmjs.org/`.
- If your organization uses a private mirror (Artifactory/Nexus), authenticate with `npm login` and verify read permissions.
- Check user/global `.npmrc` files for conflicting registry/proxy settings.


## Authentication flow

- `POST /users/` is used for registration from `/register`.
- `POST /auth/login` is used for login from `/login` using OAuth2 form fields (`username`, `password`) as `application/x-www-form-urlencoded`.
- JWT access token is stored in `localStorage` and attached as `Authorization: Bearer <token>` for subsequent API requests.
- Routes under `/` are protected and redirect unauthenticated users to `/login`.


## Implemented screens

- `/login` - Sign in form using `POST /auth/login`.
- `/register` - User registration using `POST /users/`.
- `/events` - Protected page with event list, create form, edit, and delete actions using events API endpoints.
