# Web Security Platform Backend

Django + DRF backend for a web security scanning platform.

## Implemented Scope

Backend modules and features completed:

- Core structure, env-based config, custom exception handling
- User management:
  - JWT auth (register/login/logout)
  - password reset flow
  - profile management
  - API key management
- Target management:
  - add/list/remove targets
  - ownership verification token flow
  - enable/disable scan
  - assign target to user
- Scanner integration (OWASP ZAP):
  - real ZAP REST client flow (spider, active, api import attempt, alerts fetch)
  - scan configuration + proxy fields
  - result parsing and persistence
- Scan scheduler:
  - daily/weekly/custom schedules
  - enqueue due schedules
  - worker processing + retry logic
  - queue integration with RabbitMQ
- Results & vulnerabilities:
  - vulnerability storage, severity filter, OWASP grouping
  - false-positive toggle
  - lifecycle updates
- Analytics & statistics:
  - trends, common issues, success rate, risk heatmap, time-based report
- Admin panel:
  - dashboard, user management, role assignment
  - settings management
  - audit logs
- Security:
  - multi-tenant isolation in querysets/ownership checks
  - rate limiting with admin bypass
  - admin IP whitelist permission
  - input sanitization
  - security headers (CSP/HSTS etc.)
- Blog & docs backend APIs (CRUD/search/filter/pagination/tags)
- Advanced optional APIs:
  - Postman-like API scan simulation
  - JWT vulnerability checks
  - GraphQL security checks
  - header analysis
  - AI-style risk summary endpoint

Project checklist status is tracked in `projects.md`.

## Tech Stack

- Python 3.12
- Django 6
- Django REST Framework
- SimpleJWT
- SQLite (default)
- RabbitMQ (queue)
- OWASP ZAP (scanner)
- Pytest

## Project Structure

- `apps/users` auth/profile/api-key
- `apps/targets` target management
- `apps/scans` scans, scheduler, analytics, advanced features
- `apps/core` admin panel, audit, security helpers/middleware
- `backend` project settings/urls

## Prerequisites

- Python 3.12+
- `venv` created in project root (`./venv`)
- Docker + Docker Compose

## Environment Variables

Configured in `.env` (existing file):

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `RABBITMQ_URL`
- `RABBITMQ_QUEUE`
- `ZAP_API_URL` (default `http://localhost:8090`)
- `ADMIN_IP_WHITELIST` (example: `127.0.0.1,::1,10.0.0.0/24`)

## Install

```bash
cd /home/ubuntu/Desktop/Projects/web-security/backend1
venv/bin/pip install -r requirements.txt
```

## Run Infrastructure (RabbitMQ + ZAP)

```bash
docker compose up -d rabbitmq zap
docker compose ps
```

Useful endpoints:

- RabbitMQ UI: `http://localhost:15672` (`guest/guest`)
- ZAP API: `http://localhost:8090/JSON/core/view/version/`

## Database Setup

```bash
venv/bin/python manage.py migrate
venv/bin/python manage.py seed_data
```

## Run Backend

```bash
venv/bin/python manage.py runserver
```

Base API:

- `http://127.0.0.1:8000/api/`

Docs:

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- OpenAPI JSON: `http://127.0.0.1:8000/api/schema/`

## Run Worker / Scheduler

One-time worker cycle:

```bash
venv/bin/python manage.py run_scan_worker --once
```

Continuous polling worker:

```bash
venv/bin/python manage.py run_scan_worker --sleep 3
```

Admin scheduler endpoints:

- `POST /api/scans/scheduler/enqueue/`
- `POST /api/scans/scheduler/worker-run/`

## Run Tests

Full suite:

```bash
venv/bin/pytest -q
```

Current status (latest run):

- `82 passed`

## Notes

- ZAP integration uses real REST calls; when ZAP is unavailable, client falls back safely for local flow continuity.
- Admin endpoints are protected by both `IsAdminUser` and IP whitelist checks.
- Security headers are added via middleware and Django security settings.
