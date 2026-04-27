from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_runtime_schema():
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "phone_number" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN phone_number VARCHAR(50) NULL"
            ))
        if "gender" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN gender VARCHAR(20) NULL"
            ))
        if "date_of_birth" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN date_of_birth DATETIME NULL"
            ))
        if "vehicle_details" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN vehicle_details VARCHAR(500) NULL"
            ))
        if "is_verified" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"
            ))
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
        if "rating_avg" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN rating_avg FLOAT DEFAULT 0"
            ))
        if "total_ratings" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN total_ratings INTEGER DEFAULT 0"
            ))
        if "rides_given" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN rides_given INTEGER DEFAULT 0"
            ))
        if "rides_taken" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN rides_taken INTEGER DEFAULT 0"
            ))
        if "current_lat" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN current_lat FLOAT NULL"
            ))
        if "current_lng" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN current_lng FLOAT NULL"
            ))
        if "last_location_update" not in user_columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN last_location_update DATETIME NULL"
            ))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
