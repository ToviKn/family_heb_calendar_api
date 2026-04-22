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
│   ├── lib/api/        # Axios client and API helpers
│   ├── pages/          # Route-level pages
│   ├── router/         # React Router definitions
│   └── styles/         # Global styles (Tailwind entrypoint)
├── .env.example
├── index.html
├── package.json
├── postcss.config.cjs
├── tailwind.config.ts
├── tsconfig*.json
└── vite.config.ts
```

## Local run

From repo root:

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

If `npm install` fails with HTTP 403, common fixes are:

1. Ensure npm registry is the public npm registry:

```bash
npm config set registry https://registry.npmjs.org/
```

2. Remove stale auth/proxy overrides and retry:

```bash
npm config delete _auth
npm config delete _authToken
npm config delete proxy
npm config delete https-proxy
npm cache clean --force
npm install
```

3. If your organization enforces a private registry, authenticate correctly:

```bash
npm login
```

4. If you use a company mirror (Artifactory/Nexus), verify your account has package read access.

5. Check for project/user `.npmrc` entries overriding registry or auth settings.
