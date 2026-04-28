# RemindInvoice

Automated invoice reminders — send invoices, track payments, and follow up automatically.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker | 24+ |
| Docker Compose | v2+ |
| Node.js | 20+ (local dev only) |
| Python | 3.11+ (local dev only) |

---

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/remind-invoice.git
cd remind-invoice

# 2. Create your environment file
cp .env.example .env
# Edit .env — fill in DB_PASSWORD, SECRET_KEY, SENDGRID_API_KEY, Google OAuth keys

# 3. Start all services
docker-compose up -d

# 4. Open the app
open http://localhost:3000
# API docs: http://localhost:8000/docs
```

All services (Postgres, Redis, backend API, Celery worker, frontend) start together.
The backend automatically runs `alembic upgrade head` on start.

---

## Development Setup (Hot-Reload)

```bash
# Start backing services + hot-reload API and worker
docker-compose -f docker-compose.dev.yml up -d

# The backend volume-mounts ./backend/app so code changes reload instantly.
# Run the frontend locally for fastest iteration:
cd frontend
npm install
npm run dev          # http://localhost:3000
```

To run the backend locally without Docker:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

---

## Running Tests

### Backend

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

Coverage must be >= 80% (enforced in CI).

### Frontend

```bash
cd frontend
npm test              # watch mode
npm run test:coverage # coverage report
```

### Linting

```bash
# Python
cd backend && ruff check app/ && ruff format app/ --check

# TypeScript / Next.js
cd frontend && npm run lint && npm run type-check
```

---

## Docker Commands

```bash
# Production stack
docker-compose up -d                        # start all
docker-compose down                         # stop all (data preserved)
docker-compose down -v                      # stop + delete volumes

# Development stack
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml down

# Rebuild after dependency changes
docker-compose build --no-cache backend worker

# View logs
docker-compose logs -f backend
docker-compose logs -f worker
```

---

## Service Ports

| Service | Port |
|---------|------|
| Frontend (Next.js) | 3000 |
| Backend API (FastAPI) | 8000 |
| PostgreSQL | 5432 (dev only) |
| Redis | 6379 (dev only) |

API interactive docs: http://localhost:8000/docs

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `SECRET_KEY` | Yes | JWT signing key (generate with `openssl rand -hex 32`) |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth app client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth app client secret |
| `SENDGRID_API_KEY` | Yes | SendGrid API key for email delivery |
| `FROM_EMAIL` | Yes | Sender email address |

---

## CI/CD

GitHub Actions runs on every push to `main`/`develop` and on pull requests to `main`:

1. **backend-test** — ruff lint + format check, pytest with Postgres service, coverage >= 80%
2. **frontend-test** — ESLint, TypeScript type-check, Vitest unit tests
3. **docker-build** — builds all three images (backend, worker, frontend) on `main` pushes only

See `.github/workflows/ci.yml` for the full pipeline definition.

---

## Architecture

```
remind-invoice/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Pydantic settings
│   │   ├── database.py      # SQLAlchemy engine / session
│   │   ├── models/          # ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routers/         # API route handlers
│   │   ├── services/        # Business logic
│   │   ├── auth/            # JWT + Google OAuth
│   │   └── workers/         # Celery tasks
│   ├── alembic/             # Database migrations
│   ├── tests/               # pytest test suite
│   ├── Dockerfile           # Multi-stage API image
│   └── Dockerfile.worker    # Celery worker image
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Next.js pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API client (axios)
│   │   ├── context/         # React context providers
│   │   └── types/           # TypeScript interfaces
│   └── Dockerfile           # Multi-stage Next.js image
├── docker-compose.yml       # Production stack
├── docker-compose.dev.yml   # Development stack (hot-reload)
├── .env.example             # Environment variable template
├── .gitignore
└── .github/
    └── workflows/
        └── ci.yml           # GitHub Actions CI pipeline
```
