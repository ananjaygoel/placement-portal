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

