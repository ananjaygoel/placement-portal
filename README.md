# Placement Portal Application

Flask + Jinja2 + Bootstrap + SQLite placement portal with three roles:
Admin (Institute), Company, Student.

## Local setup

```bash
cd placement-portal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Create tables + seed the predefined admin user
flask --app placement_portal init-db

# Run
flask --app placement_portal run --debug
```

### Predefined admin login (dev/demo)
- Email: `23f2001063@ds.study.iitm.ac.in`
- Password: `IITMBS`

You can override these with environment variables:
`ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SECRET_KEY`, `DATABASE_URL`.

## Notes
- The SQLite database is created programmatically (no manual DB tools).
- Core flows are implemented without JavaScript (except optional milestones).

## API (JSON)

APIs are available under `/api/*`. Auth uses the same users as the web app and
relies on the Flask session cookie (no tokens).

Example (login, then call an authenticated endpoint):

```bash
curl -c cookies.txt -X POST http://127.0.0.1:5000/api/session \\
  -H 'Content-Type: application/json' \\
  -d '{"email":"23f2001063@ds.study.iitm.ac.in","password":"IITMBS"}'

curl -b cookies.txt http://127.0.0.1:5000/api/me
```

Key endpoints:
- `POST /api/session`, `DELETE /api/session`
- `GET /api/students`, `GET|PATCH /api/students/<id>`
- `GET /api/companies`, `GET|PATCH /api/companies/<id>`
- `GET /api/drives`, `POST|PATCH|DELETE /api/drives/<id>`
- `GET|POST /api/applications`, `PATCH|DELETE /api/applications/<id>`
