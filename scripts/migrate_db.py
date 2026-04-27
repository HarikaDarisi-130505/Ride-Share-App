import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as connection:
        migrations = [
            # Original migration
            ("SHOW COLUMNS FROM ride_requests LIKE 'ride_id'",
             "ALTER TABLE ride_requests ADD COLUMN ride_id INT",
             "ALTER TABLE ride_requests ADD CONSTRAINT fk_ride_requests_ride FOREIGN KEY (ride_id) REFERENCES rides(id)",
             "ride_id in ride_requests"),
            # preferences column
            ("SHOW COLUMNS FROM rides LIKE 'preferences'",
             "ALTER TABLE rides ADD COLUMN preferences TEXT NULL",
             None,
             "preferences in rides"),
            # comfort_mode
            ("SHOW COLUMNS FROM rides LIKE 'comfort_mode'",
             "ALTER TABLE rides ADD COLUMN comfort_mode BOOLEAN DEFAULT FALSE",
             None,
             "comfort_mode in rides"),
            # women_only
            ("SHOW COLUMNS FROM rides LIKE 'women_only'",
             "ALTER TABLE rides ADD COLUMN women_only BOOLEAN DEFAULT FALSE",
             None,
             "women_only in rides"),
            # instant_booking
            ("SHOW COLUMNS FROM rides LIKE 'instant_booking'",
             "ALTER TABLE rides ADD COLUMN instant_booking BOOLEAN DEFAULT FALSE",
             None,
             "instant_booking in rides"),
            # stop_prices
            ("SHOW COLUMNS FROM rides LIKE 'stop_prices'",
             "ALTER TABLE rides ADD COLUMN stop_prices LONGTEXT NULL",
             None,
             "stop_prices in rides"),
        ]
        for check_sql, alter_sql, constraint_sql, label in migrations:
            try:
                result = connection.execute(text(check_sql))
                if not result.fetchone():
                    print("Adding: " + label)
                    connection.execute(text(alter_sql))
                    if constraint_sql:
                        connection.execute(text(constraint_sql))
                    connection.commit()
                    print("  OK: " + label + " added.")
                else:
                    print("  OK: " + label + " already exists.")
            except Exception as e:
                print("  FAILED: Migration for '" + label + "': " + str(e))

if __name__ == "__main__":
    migrate()
