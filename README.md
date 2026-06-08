# Web Security Platform — Backend

Web howpsuzlyk skanirleme platformasynyň **backend** bölegi (Django + Django REST
Framework). JWT autentifikasiýa, target/scan/vulnerability dolandyryşy, OWASP ZAP
integrasiýasy, scan scheduler, analitika, admin paneli we blog/docs API-leri.

> Frontend (Vue 3) aýratyn ammarda: `git@github.com:nedirbay/web-security.git`.
> Doly stack-y işletmek üçin aşakdaky **«Frontend bilen bilelikde»** bölümine serediň.

---

## Mazmuny
- [Tehnologiýalar](#tehnologiýalar)
- [Talaplar](#talaplar)
- [1. Gurnamak](#1-gurnamak)
- [2. Daşky gurşaw (.env)](#2-daşky-gurşaw-env)
- [3. Maglumat bazasy we seed](#3-maglumat-bazasy-we-seed)
- [4. Serweri işletmek](#4-serweri-işletmek)
- [5. Testleri işletmek](#5-testleri-işletmek)
- [6. Frontend bilen bilelikde (full-stack)](#6-frontend-bilen-bilelikde-full-stack)
- [Goşmaça: ZAP / RabbitMQ / Worker](#goşmaça-zap--rabbitmq--worker)
- [Standart ulanyjylar](#standart-ulanyjylar)
- [API resminamasy](#api-resminamasy)
- [Taslamanyň gurluşy](#taslamanyň-gurluşy)
- [Näsazlyklary düzetmek](#näsazlyklary-düzetmek)

---

## Tehnologiýalar
- Python 3.12+
- Django 4.2+ / 6.x
- Django REST Framework + SimpleJWT (JWT auth)
- SQLite (standart) — PostgreSQL hem goldanýar
- RabbitMQ (scan nobaty — islege bagly)
- OWASP ZAP (skaner — islege bagly)
- Pytest + pytest-django (testler)

## Talaplar
- **Python 3.12+** we `venv`
- (Islege bagly) **Docker + Docker Compose** — RabbitMQ we ZAP üçin

---

## 1. Gurnamak

```bash
# Ammary klonlaň
git clone git@github.com:nedirbay/web-security-backend.git
cd web-security-backend

# Wirtual gurşaw dörediň we işjeňleşdiriň
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Baglylyklary ýükläň
pip install -r requirements.txt
```

## 2. Daşky gurşaw (.env)

Ammarda eýýäm `.env` faýly bar (lokal ösüş üçin). Esasy üýtgeýjiler:

```ini
DJANGO_SECRET_KEY=...                 # önümçilikde hökman üýtgediň
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

JWT_ACCESS_TOKEN_LIFETIME=60          # minut
JWT_REFRESH_TOKEN_LIFETIME=1          # gün

RABBITMQ_URL=amqp://guest:guest@localhost:5672/%2F
RABBITMQ_QUEUE=scan_jobs
ZAP_API_URL=http://localhost:8090

# CORS — frontend origin-leri (otly bilen bölünen). Boş goýulsa standart
# dev portlary ulanylýar: 5173/3000/4173 (localhost we 127.0.0.1).
# CORS_ALLOWED_ORIGINS=http://localhost:5173
# CORS_ALLOW_ALL_ORIGINS=False
```

> **Howpsuzlyk belligi:** `CORS_ALLOW_ALL_ORIGINS=True` + credentials howpsuz däl
> kombinasiýa we brauzerler ony ret edýär. Önümçilikde anyk `CORS_ALLOWED_ORIGINS`
> allow-list ulanyň (standart sazlama hut şeýle edýär).

## 3. Maglumat bazasy we seed

```bash
# Migrasiýalary ulanyň
python manage.py migrate

# Seed: standart ulanyjylar + blog/docs (admin@guardly.com / admin123 ...)
python manage.py shell < seed_db.py

# Seed: her list endpoint üçin azyndan bir setir maglumat
# (target/scan/vulnerability/schedule/zap/apikey/setting/auditlog)
python manage.py shell < seed_fixtures.py
```

> `seed_fixtures.py` frontend contract testleriniň her endpointde maglumat tapmagy
> üçin gerek (vulnerability-ler ZAP-syz hem döredilýär).

## 4. Serweri işletmek

```bash
python manage.py runserver 127.0.0.1:8000
```

- Esasy API: `http://127.0.0.1:8000/api/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- OpenAPI JSON: `http://127.0.0.1:8000/api/schema/`

## 5. Testleri işletmek

```bash
source venv/bin/activate
python -m pytest -q
```

Soňky ýagdaý: **82 passed**. (Konfigurasiýa: `pytest.ini`, `DJANGO_SETTINGS_MODULE=backend.settings`.)

---

## 6. Frontend bilen bilelikde (full-stack)

Iki terminal ulanyň.

**Terminal A — backend:**
```bash
cd web-security-backend
source venv/bin/activate
python manage.py migrate
python manage.py shell < seed_db.py
python manage.py shell < seed_fixtures.py
python manage.py runserver 127.0.0.1:8000
```

**Terminal B — frontend** (`web-security` ammary):
```bash
cd web-security
npm install
npm run dev            # http://localhost:5173
```

Frontend `VITE_API_BASE_URL` arkaly backende baglanýar (standart
`http://localhost:8000/api/`). Standart hasap bilen giriň: `admin@guardly.com / admin123`.

**Frontend ↔ backend contract testleri** (backend işläp durka, `web-security`-de):
```bash
npm test
```
Bu testler MOCK ulanmaýar — göni janly backende baglanyp, model/endpoint laýyklygyny
barlaýar. Doly hasabat: `web-security/MODEL_UYGUNLYK_HASABATY.md`.

---

## Goşmaça: ZAP / RabbitMQ / Worker

Hakyky skanirleme we nobat üçin (islege bagly):

```bash
docker compose up -d rabbitmq zap
docker compose ps
```
- RabbitMQ UI: `http://localhost:15672` (`guest/guest`)
- ZAP API: `http://localhost:8090/JSON/core/view/version/`

> ZAP elýeterli däl bolsa, müşderi howpsuz «fallback» edýär — lokal akym dowam edýär
> (boş alert sanawy bilen).

Scan worker:
```bash
python manage.py run_scan_worker --once       # bir aýlaw
python manage.py run_scan_worker --sleep 3    # üznüksiz polling
```
Scheduler endpointleri: `POST /api/scans/scheduler/enqueue/`,
`POST /api/scans/scheduler/worker-run/`.

## Standart ulanyjylar

`seed_db.py`-den soň:

| Rol | Email | Parol |
|---|---|---|
| Admin (`is_staff=True`) | `admin@guardly.com` | `admin123` |
| Adaty ulanyjy | `user@guardly.com` | `user123` |

> Admin barlaglary `is_staff`-a esaslanýar (`IsAdminUser`). `role` meýdany
> `core.Role`-a ForeignKey (string däl).

## API resminamasy
- Swagger UI: `/api/docs/`
- OpenAPI: `/api/schema/`
- Goşmaça: `Api_endpoints.md`, `projects.md`

## Taslamanyň gurluşy
- `apps/users` — auth, profil, API key
- `apps/targets` — target dolandyryşy, eýeçilik tassyklamasy
- `apps/scans` — skanlar, scheduler, analitika, advanced funksiýalar
- `apps/core` — admin paneli, audit, howpsuzlyk kömekçileri/middleware, blog/docs
- `backend` — taslama sazlamalary/url-leri

## Näsazlyklary düzetmek
- **CORS ýalňyşy brauzerde:** `.env`-de `CORS_ALLOWED_ORIGINS`-e frontend origin-iňizi
  goşuň (mysal: `http://localhost:5173`).
- **401 / token möhleti gutardy:** access token 60 minut. Täzeden giriň ýa-da
  `JWT_ACCESS_TOKEN_LIFETIME`-y artdyryň.
- **Contract testlerde boş list:** `seed_fixtures.py`-ni ýene işlediň.
- **`runserver` kod üýtgeşmesini almaýar:** `--noreload` bilen başladan bolsaňyz,
  serweri täzeden başladyň.
