import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal

def verify_deletion():
    db = SessionLocal()
    try:
        tables = [
            "ratings",
            "ride_requests",
            "chat_messages",
            "bookings",
            "checkpoints",
            "rides",
            "users"
        ]
        
        all_empty = True
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table};")).scalar()
            print(f"Table {table}: {result} rows")
            if result > 0:
                all_empty = False
        
        if all_empty:
            print("\nVerification SUCCESS: All tables are empty.")
        else:
            print("\nVerification FAILED: Some tables still contain data.")
            
    except Exception as e:
        print(f"An error occurred during verification: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_deletion()
