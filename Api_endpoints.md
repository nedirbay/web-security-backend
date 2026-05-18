# API Endpoints

Bu faýlda proýektdäki häzirki ähli API endpointler we olaryň gysgaça maksady görkezilýär.

## Global / System

- [✅] `GET /api/schema/` - API schema (OpenAPI görnüşindäki JSON) berýär.
- [✅] `GET /api/docs/` - API dokumentasiýa UI sahypasy (Swagger stilinde).

## Admin Panel (`/api/admin/`)

- [✅] `GET /api/admin/dashboard/` - Admin dashboard statistik maglumatlary.
- [✅] `GET /api/admin/users/` - Ulanyjylaryň sanawy (admin gözegçiligi).
- [✅] `GET|PATCH|DELETE /api/admin/users/{id}/` - Belli ulanyjyny görmek/düzeltmek/pozmak.
- [✅] `POST /api/admin/users/{id}/assign-target/` - Target-y ulanyja bellemek.
- [✅] `GET /api/admin/roles/` - Rol sanawy.
- [✅] `GET|POST /api/admin/settings/` - Ulgam sazlamalaryny sanamak/döretmek.
- [✅] `GET|PATCH|DELETE /api/admin/settings/{id}/` - Ulgam sazlamasynyň detaly/düzediş/poz.
- [✅] `GET /api/admin/audit-logs/` - Audit log ýazgylary.
- [✅] `GET|POST /api/admin/blog-posts/` - Blog ýazgylaryny sanamak/döretmek.
- [✅] `GET|PATCH|DELETE /api/admin/blog-posts/{id}/` - Blog ýazgysynyň detaly/düzediş/poz.
- [✅] `GET|POST /api/admin/docs-pages/` - Dokumentasiýa sahypalaryny sanamak/döretmek.
- [✅] `GET|PATCH|DELETE /api/admin/docs-pages/{id}/` - Dokumentasiýa sahypasynyň detaly/düzediş/poz.

## Users (`/api/users/`)

- [✅] `POST /api/users/register/` - Täze ulanyjy hasaby döretmek.
- [✅] `POST /api/users/login/` - Login (token almak).
- [✅] `POST /api/users/logout/` - Logout (token/session ýapmak).
- [✅] `GET /api/users/` - Ulanyjy sanawy.
- [✅] `GET /api/users/me/` - Häzirki autentikasiýadan geçen ulanyjynyň maglumaty.
- [✅] `GET|PATCH /api/users/profile/` - Profil maglumatlaryny görmek/düzeltmek.
- [✅] `POST /api/users/password/reset/` - Parol reset soragy ugratmak.
- [✅] `POST /api/users/password/reset/confirm/` - Parol reset tassyklamak.
- [✅] `GET|POST /api/users/api-keys/` - API key sanawy/döretmek.
- [✅] `GET|DELETE /api/users/api-keys/{id}/` - API key detaly/pozmak.

## Targets (`/api/targets/`)

- [✅] `GET|POST /api/targets/` - Target sanawy we täze target döretmek.
- [✅] `GET|PATCH|DELETE /api/targets/{id}/` - Target detaly/düzediş/poz.
- [✅] `POST /api/targets/{id}/toggle-active/` - Target active/passive ýagdaýyny üýtgetmek.
- [✅] `POST /api/targets/{id}/verify-ownership/` - Target ownership barlagy.
- [✅] `POST /api/targets/{id}/assign-owner/` - Target eýesini bellemek.

## Scans (`/api/scans/`)

- [✅] `GET|POST /api/scans/` - Scan sanawy we scan ýazgysy döretmek.
- [✅] `POST /api/scans/{id}/run/` - Belli scan işledip başlatmak.
- [✅] `GET|POST /api/scans/config/zap/` - OWASP ZAP konfigurasiýalaryny sanamak/döretmek.
- [✅] `GET|POST /api/scans/schedules/` - Schedule sanawy/döretmek.
- [✅] `POST /api/scans/scheduler/enqueue/` - Scheduler arkaly nobata scan goşmak.
- [✅] `POST /api/scans/scheduler/worker-run/` - Worker tarapyndan nobatdan skan işetmek.

## Results & Vulnerabilities (`/api/scans/vulnerabilities/...`)

- [✅] `GET /api/scans/vulnerabilities/` - Vulnerability sanawy.
- [✅] `GET /api/scans/vulnerabilities/group-by-owasp/` - Vulnerability-leri OWASP kategoriýalary boýunça toparlamak.
- [✅] `POST /api/scans/vulnerabilities/{id}/false-positive/` - False positive diýip bellik etmek.
- [✅] `POST /api/scans/vulnerabilities/{id}/lifecycle/` - Vulnerability lifecycle ýagdaýyny täzelemek.

## Analytics (`/api/scans/analytics/...`)

- [✅] `GET /api/scans/analytics/vulnerability-trends/` - Wagta görä vulnerability trendi.
- [✅] `GET /api/scans/analytics/common-issues/` - Iň köp duşýan meseleler.
- [✅] `GET /api/scans/analytics/scan-success-rate/` - Scan üstünlik derejesi.
- [✅] `GET /api/scans/analytics/risk-heatmap/` - Risk heatmap maglumaty.
- [✅] `GET /api/scans/analytics/time-based-report/` - Wagt esasly hasabat.

## Advanced Features (`/api/scans/advanced/...`)

- [✅] `POST /api/scans/advanced/api-scan/` - API scan simulýasiýasy / analizi.
- [✅] `POST /api/scans/advanced/jwt-check/` - JWT gowşaklyklary barlagy.
- [✅] `POST /api/scans/advanced/graphql-scan/` - GraphQL howpsuzlyk barlagy.
- [✅] `POST /api/scans/advanced/header-analysis/` - HTTP security header analizi (CSP, HSTS we ş.m.).
- [✅] `POST /api/scans/advanced/ai-summary/` - AI esasly gysgaça risk/vulnerability düşündiriş.

---

Bellik:
- `GET|POST` ýaly ýazgy bir endpoint üçin rugsat berilýän esasy HTTP metodlaryny görkezýär.
- Käbir endpointlerde real rugsatlar (permission), rol we validasiýa görä metodyň elýeterliligi çäklendirilip bilner.
