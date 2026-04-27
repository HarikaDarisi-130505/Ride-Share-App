from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_runtime_schema():
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "two_factor_enabled" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0"
            ))
        if "driver_verified" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN driver_verified BOOLEAN DEFAULT 0"
            ))
        if "driver_verified_at" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN driver_verified_at DATETIME NULL"
            ))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
