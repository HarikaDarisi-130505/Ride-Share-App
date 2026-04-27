import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import DATABASE_URL

def clear_ride_data():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    tables_to_clear = [
        "chat_messages",
        "ratings",
        "bookings",
        "ride_requests",
        "checkpoints",
        "rides"
    ]
    
    try:
        with engine.connect() as connection:
            # Disable foreign key checks for MySQL
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            for table in tables_to_clear:
                print(f"Clearing table: {table}...")
                connection.execute(text(f"DELETE FROM {table};"))
                # Reset auto-increment
                connection.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1;"))
            
            # Re-enable foreign key checks
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            connection.commit()
            
        print("✅ Ride database cleared successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    clear_ride_data()
