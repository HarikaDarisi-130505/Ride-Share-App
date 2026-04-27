import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

columns = inspector.get_columns('ride_requests')
print("Columns in ride_requests table:")
for column in columns:
    print(f"- {column['name']}")

if 'num_seats' not in [c['name'] for c in columns]:
    print("\n[CRITICAL] num_seats column is MISSING!")
else:
    print("\n[OK] num_seats column is present.")
