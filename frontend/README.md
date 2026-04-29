# Family Calendar Frontend

A React + TypeScript frontend for the **Family Hebrew Calendar** application. It provides authenticated user flows for managing events, families, notifications, and Hebrew/Gregorian date conversion.

## 1) Project Overview

This app is the client-side dashboard for end users of the Family Calendar system.

Main implemented feature areas:

- **Authentication**: register, login, logout, and protected routes.
- **Events**: create, edit, delete, list by date, list today, list upcoming, and view details.
- **Families**: create a family, join a family, and view events for a family.
- **Notifications**: list, create, delete, mark as read, and process reminders.
- **Conversion**: convert Gregorian ⇄ Hebrew dates and fetch today in both formats.

## 2) Tech Stack

- **React 18**
- **TypeScript**
- **Vite**
- **Tailwind CSS**
- **Axios**
- **React Router**

## 3) Project Structure

```text
frontend/
├── src/
│   ├── app/                    # App shell and root app component
│   ├── components/             # Shared UI feedback components (error/success/loading/empty)
│   ├── features/auth/          # Auth context and auth state management
│   ├── layouts/                # Shared authenticated layout + navigation
│   ├── lib/
│   │   ├── api/                # Axios instance + typed API clients
│   │   ├── auth/               # Token persistence helpers
│   │   └── notifications/      # Notification formatting helpers
│   ├── pages/                  # Route pages (Login, Register, Events, Families, etc.)
│   ├── router/                 # Routing + protected route guard
│   ├── styles/                 # Global styles / Tailwind entry
│   ├── main.tsx                # React app bootstrap
│   └── vite-env.d.ts
├── .env.example
├── index.html
├── package.json
├── postcss.config.cjs
├── tailwind.config.ts
├── tsconfig*.json
└── vite.config.ts
```

## 4) Setup Instructions

### Prerequisites

- **Node.js 20+**
- **npm 10+**

### Install and run

```bash
cd frontend
npm install
npm run dev
```

Default dev URL: <http://localhost:5173>

### Environment variables

Create a `.env` file in `frontend/` (or copy from `.env.example`) and set:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 5) Available Features (User-Level)

### Authentication

- Register a new account.
- Login using email/password.
- Logout from the authenticated session.
- Protected routes redirect unauthenticated users to `/login`.

### Events

- Create events.
- Edit events.
- Delete events.
- List events by a selected date.
- View **today's** events.
- View **upcoming** events.
- Open event details page.

### Families

- Create a family.
- Join a family by family ID.
- View events for a specific family.

### Notifications

- List notifications.
- Create a notification by event ID.
- Delete notification.
- Mark notification as read.
- Process reminder notifications via backend processing endpoint.

### Conversion

- Convert **Gregorian → Hebrew** date.
- Convert **Hebrew → Gregorian** date.
- Retrieve **today's date** in both systems.

## 6) API Integration

- The frontend communicates with the backend using an Axios client configured with `VITE_API_BASE_URL`.
- After login, JWT access token is stored locally and attached to API requests as:
  - `Authorization: Bearer <token>`
- API modules are grouped under `src/lib/api` by domain (`auth`, `events`, `families`, `notifications`, `convert`, `users`).

## 7) Error Handling & UX

Implemented UX patterns include:

- **Loading states** for async actions and initial data fetches.
- **Error messages** displayed when API requests fail.
- **Success feedback** for actions such as create/update/process flows.
- **Empty states** when lists (such as notifications/events) have no data.

## 8) Scripts

From `frontend/`:

```bash
npm run dev      # start dev server
npm run build    # type-check + production build
npm run preview  # preview built app locally
npm run typecheck
```

## 9) Known Limitations

- Family membership join flow requires a numeric family ID input.
- Some pages expose backend-oriented fields (for example IDs) directly rather than using richer pickers.
- UX and visual design are functional but minimal (utility-first styling, no advanced component library).

## 10) Future Improvements (Optional)

Potential next steps:

- Add stronger form validation and field-level error mapping.
- Improve discoverability with selectors/autocomplete for entities (events/families).
- Add pagination/filters where backend supports larger datasets.
- Expand automated frontend tests (component/integration/e2e).
- Improve responsive UX polish and accessibility refinements.
