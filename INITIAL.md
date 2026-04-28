# INITIAL.md - RemindInvoice Product Definition

> A SaaS platform for freelancers to create and send invoices, automate payment reminders, and track client payment status in one place.

---

## PRODUCT

### Name
RemindInvoice

### Description
RemindInvoice helps freelancers stop chasing payments manually. Users create professional invoices, send them directly to clients, and configure automated reminder sequences that trigger before/after due dates — all with a clean dashboard showing who owes what and when.

### Target User
Freelancers (designers, developers, consultants, writers) who invoice clients and struggle with late payments and manual follow-ups.

### Type
- [x] SaaS (Software as a Service)

---

## TECH STACK

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + Python 3.11+ |
| Frontend | Next.js + TypeScript |
| Database | PostgreSQL + SQLAlchemy |
| Auth | JWT + Google OAuth |
| UI | Chakra UI |
| Payments | Dodo Payments |

---

## MODULES

### Module 1: Authentication (Required)

**Description:** User registration, login, JWT auth, and Google OAuth.

**Models:**
```
User:
  - id, email, hashed_password, full_name, is_active, is_verified
  - oauth_provider, avatar_url, created_at, updated_at

RefreshToken:
  - id, user_id (FK), token, expires_at, revoked, created_at
```

**Endpoints:**
```
POST /auth/register          - Create new account
POST /auth/login             - Login, returns access + refresh tokens
POST /auth/refresh           - Exchange refresh token for new access token
POST /auth/logout            - Revoke refresh token
GET  /auth/me                - Get current user profile
PUT  /auth/me                - Update profile
POST /auth/google            - Initiate Google OAuth
GET  /auth/google/callback   - Google OAuth callback
POST /auth/forgot-password   - Send reset link
POST /auth/reset-password    - Reset with token
```

**Pages:**
```
/login                - Login with email + Google button
/register             - Registration form
/forgot-password      - Request password reset
/reset-password       - New password form (token-gated)
/profile              - User profile settings (protected)
```

---

### Module 2: Clients

**Description:** Manage client profiles, contact information, and payment history per client.

**Models:**
```
Client:
  - id, user_id (FK)
  - name, email, phone, company_name
  - address_line1, address_line2, city, state, postal_code, country
  - payment_terms_days, currency, notes, is_active
  - created_at, updated_at
```

**Endpoints:**
```
GET    /clients           - List all clients (search/filter)
POST   /clients           - Create new client
GET    /clients/{id}      - Client detail + invoice summary
PUT    /clients/{id}      - Update client
DELETE /clients/{id}      - Soft-delete client
GET    /clients/{id}/invoices - List invoices for a client
```

**Pages:**
```
/clients              - Client list with search
/clients/new          - Create client form
/clients/[id]         - Client detail with invoice history
/clients/[id]/edit    - Edit client form
```

---

### Module 3: Invoices

**Description:** Create professional invoices with line items, send to clients via email with PDF, and track payment status.

**Models:**
```
Invoice:
  - id, user_id (FK), client_id (FK), invoice_number
  - status: draft | sent | viewed | paid | overdue | cancelled
  - issue_date, due_date
  - subtotal, tax_rate, tax_amount, discount_amount, total, currency
  - notes, pdf_url, public_token
  - sent_at, paid_at, created_at, updated_at

InvoiceItem:
  - id, invoice_id (FK)
  - description, quantity, unit_price, amount, sort_order
```

**Endpoints:**
```
GET    /invoices                    - List invoices (filter by status/client/date)
POST   /invoices                    - Create new invoice (draft)
GET    /invoices/{id}               - Invoice detail with items
PUT    /invoices/{id}               - Update invoice (draft only)
DELETE /invoices/{id}               - Delete invoice (draft only)
POST   /invoices/{id}/send          - Send to client via email + generate PDF
POST   /invoices/{id}/mark-paid     - Mark as paid
POST   /invoices/{id}/duplicate     - Duplicate invoice
GET    /invoices/{id}/pdf           - Download PDF
GET    /invoices/public/{token}     - Public client view (no auth)
```

**Pages:**
```
/invoices                   - Invoice list with status tabs (All/Draft/Sent/Overdue/Paid)
/invoices/new               - Invoice creation form with line items
/invoices/[id]              - Invoice detail / preview
/invoices/[id]/edit         - Edit draft invoice
/invoice/view/[token]       - Public client-facing invoice view
```

---

### Module 4: Reminders

**Description:** Automated and manual payment reminder emails triggered by invoice due dates.

**Models:**
```
ReminderRule:
  - id, user_id (FK)
  - name, trigger_type: before_due | on_due | after_due
  - days_offset, is_active
  - created_at, updated_at

ReminderLog:
  - id, invoice_id (FK), rule_id (FK, nullable for manual)
  - sent_at, status: sent | failed
  - email_to, subject
```

**Endpoints:**
```
GET    /reminders/rules             - List user's reminder rules
POST   /reminders/rules             - Create new rule
PUT    /reminders/rules/{id}        - Update rule
DELETE /reminders/rules/{id}        - Delete rule
POST   /reminders/send/{invoice_id} - Manually trigger reminder
GET    /reminders/logs              - Full reminder send history
GET    /reminders/logs/{invoice_id} - History for specific invoice
```

**Pages:**
```
/reminders          - Reminder rules list + upcoming scheduled reminders
/reminders/settings - Configure rules and email templates
```

---

### Module 5: Dashboard & Analytics

**Description:** Overview of revenue, outstanding amounts, recent activity, and payment trends.

**Endpoints:**
```
GET /dashboard/stats            - Key metrics (billed/paid/outstanding/overdue count)
GET /dashboard/recent-invoices  - Last 5 invoices
GET /dashboard/revenue-chart    - Monthly revenue for last 12 months
GET /dashboard/overdue          - Overdue invoice list
```

**Pages:**
```
/dashboard    - Stats cards, revenue chart, overdue alerts, recent invoices
/settings     - Preferences, notification settings, invoice defaults
```

---

### Module 6: Admin Panel

**Description:** Admin-only interface for user management, platform metrics, and audit logging.

**Models:**
```
AdminLog:
  - id, admin_user_id (FK), action, target_type, target_id
  - metadata (JSON), created_at
```

**Endpoints:**
```
GET /admin/users            - List all users (paginated/searchable)
GET /admin/users/{id}       - User detail + usage stats
PUT /admin/users/{id}/status - Activate/deactivate user
GET /admin/stats            - Platform metrics
GET /admin/logs             - Admin audit log
```

**Pages:**
```
/admin              - Admin dashboard (protected, admin role only)
/admin/users        - User management table
/admin/users/[id]   - Individual user detail
```

---

## ADDITIONAL FEATURES

### Email Notifications (via SendGrid or Resend)
- Welcome email on registration
- Invoice sent confirmation to freelancer
- Invoice email to client with PDF attachment + public view link
- Payment reminder emails to clients
- Payment received notification to freelancer
- Password reset email

### PDF Generation (WeasyPrint or ReportLab)
- Generate PDF from invoice data
- Store PDF in file storage
- Download link on invoice detail page
- Attach PDF when emailing invoice to client

### File Uploads
- User avatar upload
- Optional invoice attachments (supporting documents)
- Store in local filesystem or S3-compatible bucket

---

## MVP SCOPE

### Must Have (MVP)
- [x] User registration and login (email/password + Google OAuth)
- [x] Create and manage clients
- [x] Create invoices with line items and send via email
- [x] Automated payment reminders based on due date rules
- [x] Mark invoices as paid / track payment status
- [x] PDF invoice generation and download
- [x] Basic dashboard with key metrics

### Nice to Have (Post-MVP)
- [ ] Admin panel
- [ ] File attachments on invoices
- [ ] Full revenue analytics charts
- [ ] Dodo Payments subscription billing for the platform
- [ ] Client portal (self-service payment page)
- [ ] Recurring invoices
- [ ] Multi-currency support
- [ ] Invoice templates / branding

---

## ACCEPTANCE CRITERIA

### Authentication
- [ ] User can register with email and password
- [ ] User can login with Google OAuth
- [ ] JWT access token expires in 30 minutes
- [ ] Refresh token extends session up to 7 days
- [ ] Protected routes redirect unauthenticated users to /login
- [ ] Password reset flow works end-to-end via email

### Clients
- [ ] User can create, edit, and deactivate clients
- [ ] Client email must be unique per user
- [ ] Client detail page shows invoice history and outstanding amount

### Invoices
- [ ] User can create invoice with multiple line items
- [ ] Invoice total auto-calculates from items + tax + discount
- [ ] Invoice number auto-increments per user (INV-001, INV-002...)
- [ ] Sending invoice generates PDF and emails the client
- [ ] Public client view link works without authentication
- [ ] Only draft invoices can be edited or deleted
- [ ] Overdue status updates automatically based on due date

### Reminders
- [ ] User can create reminder rules (e.g. "3 days before due", "1 day after due")
- [ ] Reminder emails fire automatically via scheduled background job
- [ ] User can manually trigger a reminder for any sent invoice
- [ ] Reminder send history is logged per invoice

### Dashboard
- [ ] Stats cards show: total billed, total paid, outstanding, overdue count
- [ ] Recent invoices list is up to date
- [ ] Overdue invoices highlighted with a quick-action button

### Quality
- [ ] All API endpoints documented in OpenAPI (auto-generated by FastAPI)
- [ ] Backend test coverage 80%+
- [ ] Frontend TypeScript strict mode passes with zero errors
- [ ] Docker builds and runs successfully
- [ ] All forms have validation with helpful error messages

---

## SPECIAL REQUIREMENTS

### Security
- [x] Rate limiting on auth endpoints (max 5 attempts per 15 min)
- [x] Input validation and sanitization on all endpoints
- [x] SQL injection prevention via SQLAlchemy ORM
- [x] XSS prevention via Next.js / React default escaping
- [x] CSRF protection on Google OAuth state parameter
- [x] Invoice public tokens must be cryptographically random (UUID v4)
- [x] PDF download links must verify invoice ownership

### Background Jobs
- Celery + Redis for scheduled tasks
- Daily job to auto-update invoice status to "overdue" when past due date
- Reminder rule engine runs daily, checks pending rules and fires emails

### Integrations
- [x] Email: SendGrid or Resend (transactional)
- [x] PDF: WeasyPrint or ReportLab
- [x] Google OAuth 2.0
- [ ] Dodo Payments (post-MVP for platform subscription billing)

---

## AGENTS

| Agent | Role | Works On |
|-------|------|----------|
| DATABASE-AGENT | Creates all models and migrations | User, Client, Invoice, InvoiceItem, ReminderRule, ReminderLog, AdminLog |
| BACKEND-AGENT | Builds API endpoints and services | All 6 modules + background jobs + email + PDF |
| FRONTEND-AGENT | Creates UI pages and components | All modules' Next.js pages with Chakra UI |
| DEVOPS-AGENT | Sets up Docker, Celery, Redis, CI/CD | Infrastructure + environment config |
| TEST-AGENT | Writes unit and integration tests | All backend services + API endpoints |
| REVIEW-AGENT | Security and code quality audit | All code |

---

# READY?

```bash
/generate-prp INITIAL.md
```

Then:

```bash
/execute-prp PRPs/remindinvoice-prp.md
```
