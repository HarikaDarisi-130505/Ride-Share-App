import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal, engine
from app.models import Base

def delete_all_data():
    db = SessionLocal()
    try:
        print("Starting data deletion...")
        
        # Disable foreign key checks for MySQL
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        # Tables to truncate in order
        tables = [
            "ratings",
            "ride_requests",
            "chat_messages",
            "bookings",
            "checkpoints",
            "rides",
            "users"
        ]
        
        for table in tables:
            print(f"Truncating table: {table}")
            db.execute(text(f"TRUNCATE TABLE {table};"))
        
        # Re-enable foreign key checks
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        
        db.commit()
        print("All user data has been deleted successfully.")
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_data()
