# CLAUDE.md - RemindInvoice Project Rules

> Project-specific rules for Claude Code. This file is read automatically in every conversation.

---

## Project Overview

**Project Name:** RemindInvoice
**Description:** SaaS for freelancers to create invoices, send them to clients, and automate payment reminders.
**Target User:** Freelancers who struggle with late payments and manual follow-ups.

**Tech Stack:**
- Backend: FastAPI + Python 3.11+
- Package Manager: uv (pyproject.toml + uv.lock)
- Frontend: Next.js + TypeScript
- Database: PostgreSQL + SQLAlchemy
- Auth: JWT + Google OAuth 2.0
- UI: Chakra UI
- Payments: Dodo Payments
- Background Jobs: Celery + Redis
- Email: SendGrid or Resend
- PDF: WeasyPrint or ReportLab

---

## Project Structure

```
remind-invoice/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── client.py
│   │   │   ├── invoice.py
│   │   │   ├── reminder.py
│   │   │   └── admin.py
│   │   ├── schemas/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── clients.py
│   │   │   ├── invoices.py
│   │   │   ├── reminders.py
│   │   │   ├── dashboard.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── email.py
│   │   │   ├── pdf.py
│   │   │   └── reminder_scheduler.py
│   │   ├── auth/
│   │   └── workers/           # Celery tasks
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   │   ├── (auth)/        # login, register, etc.
│   │   │   ├── dashboard/
│   │   │   ├── invoices/
│   │   │   ├── clients/
│   │   │   ├── reminders/
│   │   │   ├── settings/
│   │   │   └── admin/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/          # API client functions
│   │   ├── context/
│   │   └── types/
│   └── package.json
├── .claude/
│   └── commands/
├── skills/
├── agents/
├── PRPs/
├── INITIAL.md
└── docker-compose.yml
```

---

## Code Standards

### Python (Backend)
```python
# ALWAYS use type hints on all functions
def get_invoice(db: Session, invoice_id: int, user_id: int) -> Invoice:
    pass

# ALWAYS use async endpoints
@router.get("/invoices/{id}")
async def get_invoice(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pass

# Use logging, never print()
import logging
logger = logging.getLogger(__name__)
logger.info("Invoice %s sent to client", invoice_id)
```

### TypeScript (Frontend)
```typescript
// ALWAYS define interfaces — NO any types
interface Invoice {
  id: number;
  invoiceNumber: string;
  status: "draft" | "sent" | "viewed" | "paid" | "overdue" | "cancelled";
  total: number;
  dueDate: string;
  client: Client;
}

// Async functions must have explicit return types
const sendInvoice = async (id: number): Promise<Invoice> => { ... };
```

---

## Forbidden Patterns

### Backend
- `print()` — use `logging` module
- Plain text passwords — use `bcrypt`
- Hardcoded secrets — use environment variables via `config.py`
- Raw SQL strings — use SQLAlchemy ORM
- Skipping input validation — all endpoints must use Pydantic schemas
- Missing `user_id` filter — all queries must scope to the current user

### Frontend
- `any` type — always define proper interfaces
- `console.log` in production code
- Inline `style={{}}` — use Chakra UI props or `sx`
- Unhandled async errors — always use try/catch with user feedback
- Hardcoded API URLs — use `NEXT_PUBLIC_API_URL` env var

---

## Module-Specific Rules

### Invoices
- Invoice number format: `INV-YYYYMM-XXXX` (auto-generated, never user-set)
- Valid statuses: `draft`, `sent`, `viewed`, `paid`, `overdue`, `cancelled`
- Only `draft` invoices may be edited or deleted
- Public token must be a UUID v4, generated on invoice creation
- PDF must be regenerated if invoice content changes before sending
- When sending, always update `sent_at` and flip status to `sent`

### Reminders
- `trigger_type` must be: `before_due`, `on_due`, or `after_due`
- `days_offset` must be >= 0; for `before_due` it means N days before due date
- Never send reminders for `paid` or `cancelled` invoices
- Log every reminder attempt (success or failure) in `ReminderLog`

### Clients
- `email` must be unique per user (not globally)
- Deleting a client is a soft delete (`is_active = False`)
- Cannot delete a client with non-cancelled invoices

### Auth
- Access token TTL: 30 minutes
- Refresh token TTL: 7 days
- Google OAuth must validate `state` parameter to prevent CSRF
- Always hash passwords with bcrypt (cost factor 12+)

---

## API Conventions

- All endpoints prefixed: `/api/v1/`
- Resources use plural nouns: `/invoices`, `/clients`, `/reminders`
- Current user's resources only — always filter by `user_id`
- HTTP status codes:
  - `200` Success, `201` Created, `204` Deleted
  - `400` Bad Request, `401` Unauthorized, `403` Forbidden
  - `404` Not Found, `409` Conflict, `422` Validation Error

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/remindinvoice

# Auth
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Email
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=hello@remindinvoice.com

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# File Storage
UPLOAD_DIR=./uploads

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Development Commands

```bash
# Backend — first-time setup (creates .venv and installs all deps)
cd backend
uv sync                          # creates .venv + installs from uv.lock

# Run the API
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# Celery worker  (separate terminal)
uv run celery -A app.workers.celery_app worker --loglevel=info

# Celery beat scheduler  (separate terminal)
uv run celery -A app.workers.celery_app beat --loglevel=info

# Add a new dependency
uv add <package>                 # updates pyproject.toml + uv.lock

# Add a dev-only dependency
uv add --group dev <package>

# Frontend
cd frontend
npm install
npm run dev

# Docker (full stack)
docker-compose up -d

# Tests
uv run pytest tests/ -v --cov=app --cov-report=term-missing

# Linting
uv run ruff check . && uv run ruff format .
cd frontend && npm run lint && npm run type-check
```

---

## Commit Message Format

```
feat(invoices): add PDF generation on send
fix(reminders): prevent sending for paid invoices
refactor(auth): extract token logic into service
test(clients): add soft-delete coverage
docs: update environment variable list
```

---

## Workflow

```
1. Edit INITIAL.md (already done)
2. /generate-prp INITIAL.md
3. /execute-prp PRPs/remindinvoice-prp.md
```

---

## Skills Reference

| Task | Skill |
|------|-------|
| Database models | `skills/DATABASE.md` |
| API + Auth | `skills/BACKEND.md` |
| React/Next.js + UI | `skills/FRONTEND.md` |
| Testing | `skills/TESTING.md` |
| Docker + CI/CD | `skills/DEPLOYMENT.md` |

---

## Agents

| Agent | Role |
|-------|------|
| DATABASE-AGENT | Models + Alembic migrations |
| BACKEND-AGENT | FastAPI routes + services + Celery tasks |
| FRONTEND-AGENT | Next.js App Router pages + Chakra UI |
| TEST-AGENT | pytest unit + integration tests |
| REVIEW-AGENT | Security audit + code quality |
| DEVOPS-AGENT | Docker + docker-compose + CI/CD |
