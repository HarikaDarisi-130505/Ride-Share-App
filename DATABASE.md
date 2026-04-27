# Backend Database

The official backend database for this project is MySQL.

Active source of truth:
- Runtime connection: `backend/.env` via `DATABASE_URL`
- Runtime mode and backend URL: `backend/.env` via `APP_ENV` and `PUBLIC_API_BASE_URL`
- SQLAlchemy engine: `backend/app/database.py`
- Alembic migrations: `backend/alembic/env.py`

Expected database:
- Database name: `rideshare_db`
- Driver format: `mysql+pymysql://root:<password>@localhost/rideshare_db`

Legacy SQLite files from earlier experiments have been moved to `backend/archive/sqlite-legacy/`.
They are kept only for reference and are not used by the current backend.
