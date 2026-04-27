import sys
import os

# Add path to import app modules
sys.path.append(str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from app import schemas, auth, models, database
from pydantic import ValidationError

def test_register_logic():
    print("1. Testing Pydantic Schema Validation (EmailStr)...")
    try:
        user_data = schemas.RegisterRequest(
            name="Test User",
            email="test@example.com",
            password="password123"
        )
        print("[OK] Schema validation passed.")
    except Exception as e:
        print(f"[FAIL] Schema validation failed: {e}")
        return

    print("\n2. Testing Password Hashing...")
    try:
        hashed = auth.get_password_hash(user_data.password)
        print(f"[OK] Password hashed: {hashed[:10]}...")
    except Exception as e:
        print(f"[FAIL] Password hashing failed: {e}")
        return

    print("\n3. Testing Database Insertion...")
    db = next(database.get_db())
    try:
        # Check if user exists first to avoid duplicate error
        existing = db.query(models.User).filter(models.User.email == user_data.email).first()
        if existing:
            print("[INFO] User already exists, cleaning up for test...")
            db.delete(existing)
            db.commit()

        new_user = models.User(
            email=user_data.email,
            hashed_password=hashed,
            full_name=user_data.name
        )
        db.add(new_user)
        db.commit()
        print("[OK] User inserted into Database successfully!")
    except Exception as e:
        print(f"[FAIL] Database insertion failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_register_logic()
