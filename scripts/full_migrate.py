import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import engine
from sqlalchemy import text, inspect

def sync_schema():
    inspector = inspect(engine)
    
    tables_to_columns = {
        "users": [
            ("role", "VARCHAR(50) DEFAULT 'passenger'"),
            ("phone_number", "VARCHAR(20)"),
            ("vehicle_details", "VARCHAR(500)"),
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("rating_avg", "FLOAT DEFAULT 0.0"),
            ("total_ratings", "INT DEFAULT 0"),
            ("rides_given", "INT DEFAULT 0"),
            ("rides_taken", "INT DEFAULT 0"),
            ("current_lat", "FLOAT"),
            ("current_lng", "FLOAT"),
            ("last_location_update", "DATETIME")
        ],
        "rides": [
            ("origin_lat", "FLOAT"),
            ("origin_lng", "FLOAT"),
            ("destination_lat", "FLOAT"),
            ("destination_lng", "FLOAT"),
            ("price", "FLOAT"),
            ("route_polyline", "TEXT"),
            ("status", "VARCHAR(50) DEFAULT 'scheduled'"),
            ("started_at", "DATETIME"),
            ("completed_at", "DATETIME")
        ],
        "ride_requests": [
            ("ride_id", "INT"),
            ("origin", "VARCHAR(255)"),
            ("destination", "VARCHAR(255)")
        ]
    }

    with engine.connect() as conn:
        for table_name, columns in tables_to_columns.items():
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            for col_name, col_type in columns:
                if col_name not in existing_columns:
                    print(f"Adding column {col_name} to table {table_name}...")
                    try:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        print(f"Successfully added {col_name}.")
                    except Exception as e:
                        print(f"Error adding {col_name}: {e}")
                else:
                    print(f"Column {col_name} already exists in {table_name}.")

if __name__ == "__main__":
    sync_schema()
