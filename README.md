# Finance Tracker

A deliberately small personal expense & budget tracker. Single user role —
every logged-in user only ever sees their own categories, transactions and
budgets. React + Vite + TypeScript frontend, Django REST Framework backend,
PostgreSQL database. No Celery/Redis — there is no background work to run.

## Data model

- **User** — Django's `AbstractUser` with `email` as `USERNAME_FIELD`. No
  profile model; single role.
- **Category** — `user`, `name`, `type` (`income`/`expense`), unique
  `(user, name)`.
- **Transaction** — `user`, `category`, `amount`, `type`, `date`, `note`,
  `created_at`. A transaction's `type` must match its category's `type`
  (enforced in the serializer, returns 400 on mismatch).
- **Budget** — `user`, `category` (must be an expense category), `month`,
  `limit_amount`, unique `(user, category, month)`. `month` is a `DateField`
  always normalised to the first day of the month (e.g. `2026-01-01` means
  "January 2026") — chosen over a `year`+`month` int pair so it reuses the
  same `__year`/`__month` filtering already used for `Transaction.date`.

## REST API

- `POST /api/auth/register/`, `POST /api/auth/login/` (JWT),
  `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/auth/me/`
- `/api/categories/` — list/create/retrieve/update/delete, `?type=`
- `/api/transactions/` — list/create/retrieve/update/delete,
  `?month=YYYY-MM`, `?category=`, `?type=`
- `/api/budgets/` — list/create/retrieve/update/delete, `?month=YYYY-MM`
- `GET /api/dashboard/?month=YYYY-MM` (defaults to current month) — total
  income, total expenses, net, and a per-expense-category breakdown
  (`spent`, and `budget_limit`/`remaining` for any category that has a
  budget for that month; categories with spending but no budget show
  `spent` only, with `budget_limit`/`remaining` as `null`).

Every ViewSet scopes its queryset to `request.user` — there is no
cross-user access even by guessing another user's object ID.

## Running locally with Docker (Postgres)

```bash
cp .env.example .env
docker compose up --build
```

Backend on http://localhost:8000, frontend on http://localhost:5173.

## Running the backend without Docker (dev-only SQLite override)

No Postgres/Docker needed for this — same `USE_SQLITE` pattern used by the
sibling apps in this workspace. **Never set `USE_SQLITE=True` in
docker-compose or production.**

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt

export USE_SQLITE=True
export DJANGO_SETTINGS_MODULE=config.settings.dev

python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Running the frontend

```bash
cd frontend
npm install
npm run dev      # dev server on :5173
npm run build    # production build (tsc -b && vite build)
```

Set `VITE_API_BASE_URL` (see `frontend/.env.example`) if the backend isn't
at `http://localhost:8000/api`.

## Auth trade-off (dev-only)

The access token is kept in memory only; the refresh token is kept in
`localStorage` and the client refreshes on a 401. A real deployment would
instead issue the refresh token as an httpOnly cookie from the backend —
this simplified pattern (same as the sibling apps in this workspace) is a
deliberate trade-off for a small demo app, not a recommendation for
production.
