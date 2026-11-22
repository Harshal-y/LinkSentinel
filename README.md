# LinkSentinel 2.3 — Supabase-ready deployment

LinkSentinel is a Flask-based URL security analyzer. This package supports:
- Local development with SQLite.
- Hosted deployment with Supabase PostgreSQL.
- User registration/login, per-user scan history, analytics dashboard and PDF reports.
- DNS/TLS/HTTP inspection, URL heuristics and optional URLhaus lookups.

## 1. Requirements

- Python 3.11 or newer (Python 3.12 recommended).
- A Supabase project and its PostgreSQL **Session Pooler** connection URI.
- A Render account and GitHub repository for hosted deployment.

## 2. Configure Supabase

1. Open your Supabase project.
2. Choose **Connect → Direct → Connection string**.
3. Select **URI**. For Render, use the **Session pooler** URI if your runtime needs IPv4.
4. Copy the URI. It should resemble:

   `postgresql://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres`

5. Replace the password placeholder locally in your `.env` file. If the password contains URL-reserved characters, percent-encode them.
6. Do not share or commit the URI.

The application creates its `users` and `scans` tables and index automatically on startup when `DATABASE_URL` is configured. It uses TLS (`sslmode=require`) if no SSL mode is already present.

## 3. Run locally

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set:

```env
SECRET_KEY=your-long-random-secret
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres
COOKIE_SECURE=0
```

To generate a Flask secret:

```powershell
py -c "import secrets; print(secrets.token_hex(32))"
```

Start:

```powershell
python app.py
```

Open http://127.0.0.1:5000

If `DATABASE_URL` is blank, the application uses local SQLite (`linksentinel.db`). If it is set, it uses Supabase PostgreSQL.

## 4. Optional: migrate existing SQLite users and scans

The uploaded project archive contained a local SQLite database. For safety, database files and `.env` secrets are not included in this deployment package. If you want to transfer your existing local accounts and scan history:

1. Keep your original `linksentinel.db` in this project root.
2. Configure `DATABASE_URL` in `.env`.
3. Install requirements.
4. Run:

```powershell
python migrate_sqlite_to_supabase.py
```

Run this once against an empty/new Supabase database. It preserves user IDs, password hashes, scan IDs and scan records. Back up the SQLite database first. Do not run this repeatedly after users have started creating records in Supabase unless you understand the conflict handling.

## 5. Deploy on Render

### Push to GitHub

Create a **private** GitHub repository and upload the project contents. `.gitignore` excludes `.env`, SQLite databases, virtual environments and Python cache files.

### Create the Render service

1. Sign in at https://render.com.
2. Select **New → Blueprint** and connect the GitHub repository containing `render.yaml`, or create a Web Service manually.
3. For a manual Web Service, use:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --workers 1 --threads 4 --timeout 30 --bind 0.0.0.0:$PORT app:app`
4. Configure environment variables:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Generate a long random value (or use Render's generated value from the Blueprint) |
| `DATABASE_URL` | Supabase Session Pooler URI |
| `COOKIE_SECURE` | `1` |
| `URLHAUS_AUTH_KEY` | Optional URLhaus Auth-Key; omit/leave unset to disable |

5. Deploy. Check Render logs and open `/health`; it should return a JSON status response.
6. Register a test account and verify scanning, dashboard, scan history and PDF download.

**Cost note:** `render.yaml` currently selects the `starter` plan. Check Render's current pricing before creating the service. You can change the plan in Render if appropriate.

## 6. Optional URLhaus integration

Set `URLHAUS_AUTH_KEY` in Render or `.env` to enable URLhaus lookups. Leave it unset to disable the external lookup. The scanner remains functional without this key.

## 7. Docker (optional)

```bash
docker build -t linksentinel .
docker run --env-file .env -p 10000:10000 linksentinel
```

## 8. Important security notes before public launch

This is an academic project, not a fully audited production security service. A public URL scanner can be abused as an SSRF/network-probing proxy. Before opening it to untrusted users, conduct a security review and add/verify:
- Robust SSRF protection, including DNS rebinding checks at connection time and redirect destination validation.
- Strict outbound network egress controls.
- Shared rate limiting (the current in-process limiter is not shared between multiple instances).
- Monitoring, abuse reporting and operational limits.
- Secure secret management and database backups.
- A production security review of authentication, session handling and dependency versions.

Do not claim that a low-risk result proves a website is safe. URLhaus no-match results also do not prove safety.

## 9. Tests

```bash
python -m unittest tests.py -v
```

The included tests are offline smoke tests for URL validation, basic heuristics, IP classification and the health endpoint. They do not validate remote TLS behavior or live Supabase connectivity.

## 10. Supabase keys

This Flask backend connects directly to PostgreSQL using `DATABASE_URL`. It does **not** require the Supabase publishable/anon key or service-role key. Do not put a service-role key in browser code. The `URLHAUS_AUTH_KEY` is unrelated and only enables the optional URLhaus service.
