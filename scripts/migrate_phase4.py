import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE ride_requests ADD COLUMN num_seats INT DEFAULT 1"))
        print("[OK] Column num_seats added successfully.")
    except Exception as e:
        print(f"[ERROR] Could not add column: {e}")
