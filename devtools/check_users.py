import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app import models

db = SessionLocal()
users = db.query(models.User).all()

print(f"Total users found: {len(users)}")
for user in users:
    print(f"ID: {user.id}, Name: {user.full_name}, Email: {user.email}")

db.close()
