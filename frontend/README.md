# Family Calendar Frontend

React + Vite frontend for Family Calendar.

## Project Structure

```text
frontend/
├── src/
│   ├── app/                # App shell composition (root App component)
│   ├── features/           # Feature-scoped modules (e.g., auth context/state)
│   ├── components/         # Shared UI components used across pages
│   ├── pages/              # Route-level screens
│   ├── router/             # App routing and protected-route logic
│   ├── layouts/            # Reusable page/layout wrappers
│   ├── lib/
│   │   ├── api/            # Typed API client layer (axios instance + endpoint modules)
│   │   ├── auth/           # Client auth helpers (token storage)
│   │   ├── i18n/           # Internationalization setup and locale dictionaries
│   │   └── notifications/  # Notification formatting/helpers
│   ├── styles/             # Global styles and Tailwind/CSS entrypoints
│   └── main.tsx            # SPA bootstrap
├── package.json            # Frontend scripts and dependencies
├── vite.config.ts          # Vite bundler/runtime config
├── tailwind.config.ts      # Tailwind config
└── .env.example            # Frontend env template
```

### Frontend architecture areas

- **Feature layer (`src/features`)**: Encapsulates stateful business concerns (currently auth flow/context).
- **Shared UI (`src/components`, `src/layouts`)**: Reusable presentation and composition primitives.
- **API layer (`src/lib/api`)**: Centralized HTTP client, typed request/response contracts, and endpoint modules.
- **Auth flow (`src/features/auth`, `src/lib/auth`, `src/router/ProtectedRoute.tsx`)**: Token persistence, auth context, and route protection.
- **Routing/pages (`src/router`, `src/pages`)**: URL mapping and top-level page experiences.

## Environment variables
Copy `.env.example` and configure:

- `VITE_API_BASE_URL` – Backend API URL
- Additional Vite environment variables as needed

## Development
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

## Build

Creates an optimized production build in the `dist/` directory.

```bash
npm run build
```

## Deployment
- Vercel: configure frontend env values to target deployed backend API.
- Ensure backend CORS `ALLOWED_ORIGINS` includes your Vercel domain.
