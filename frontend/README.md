# Family Calendar Frontend

Frontend application for the **Family Hebrew Calendar** platform. This app lets authenticated users manage family events, notifications, and date conversion between Gregorian and Hebrew calendars.

---

## Overview

The frontend provides these implemented user workflows:

- **Authentication**: register, login, logout, protected routes
- **Events**: create, edit, delete, list by date, today, upcoming, details
- **Families**: create family, join family, view family events
- **Notifications**: list, create, delete, mark as read, process reminders
- **Conversion**: Gregorian ↔ Hebrew conversion, plus “today” in both formats

---

## Tech Stack

- **React 18 + TypeScript** (Vite)
- **Tailwind CSS**
- **Axios**
- **React Router**

---

## Project Structure

```text
frontend/
├── src/
│   ├── app/                  # App shell
│   ├── components/           # Shared UI feedback components
│   ├── features/auth/        # Auth context/state
│   ├── layouts/              # Shared authenticated layout/navigation
│   ├── lib/
│   │   ├── api/              # Axios client + typed API modules
│   │   ├── auth/             # Token storage helpers
│   │   └── notifications/    # Notification format helpers
│   ├── pages/                # Route pages
│   ├── router/               # Router + route protection
│   └── styles/               # Global styles (Tailwind entry)
├── .env.example
├── package.json
└── vite.config.ts
```

---

## Setup

### Prerequisites

- Node.js **20+**
- npm **10+**

### Install & run

```bash
cd frontend
npm install
npm run dev
```

App runs by default at: `http://localhost:5173`

### Environment variables

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## API Integration

- All API calls use a shared Axios client configured with `VITE_API_BASE_URL`.
- After login, the JWT access token is stored and sent on requests as:

```http
Authorization: Bearer <token>
```

- Domain clients are organized under `src/lib/api` (`auth`, `users`, `events`, `families`, `notifications`, `convert`).

---

## Feature Highlights (with examples)

### Authentication

- Register via `/register`
- Login via `/login`
- Logout from the home/dashboard
- Protected pages redirect unauthenticated users to login

### Events

- Manage events from `/events`
- Switch list mode: date / today / upcoming
- Open details from `/events/:id`

Example API paths used:

```text
POST   /events/
GET    /events/
GET    /events/today
GET    /events/upcoming
GET    /events/{id}
PUT    /events/{id}
DELETE /events/{id}
```

### Families

- Create family in `/families`
- Join family using numeric family ID
- Fetch family-specific events

Example API paths used:

```text
POST /families/
POST /families/{family_id}/members
GET  /events/family/{family_id}
```

### Notifications

- View notifications in `/notifications`
- Create notification by event ID
- Mark as read / delete
- Trigger reminder processing

Example API paths used:

```text
GET    /notifications/
POST   /notifications/
PATCH  /notifications/{notification_id}/read
DELETE /notifications/{notification_id}
POST   /notifications/reminders/process
```

### Conversion

- Convert Gregorian → Hebrew
- Convert Hebrew → Gregorian
- Get today in both formats

Example API paths used:

```text
GET /convert/hebrew
GET /convert/gregorian
GET /convert/today
```

---

## UX and Error Handling

The UI includes:

- Loading indicators for async actions
- Error and success messages for user actions
- Empty-state messages when lists have no data

---

## Scripts

```bash
npm run dev       # Start development server
npm run build     # Type-check and build for production
npm run preview   # Preview production build
npm run typecheck # Run TypeScript checks
```

---

## Known Limitations

- Family join and some notification flows require manual numeric IDs.
- UI is intentionally lightweight and functional (no advanced component framework).

---

## Future Improvements

- Better form validation and inline field-level errors
- Entity pickers/autocomplete instead of manual IDs
- Expanded frontend test coverage (component/integration/e2e)
- Additional accessibility and responsive UX refinements
