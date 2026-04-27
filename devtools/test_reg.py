import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app import models, auth

def test_registration():
    db = SessionLocal()
    try:
        # Check if user already exists
        email = "test@example.com"
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            print(f"User {email} already exists.")
            return

        # Try to create user
        new_user = models.User(
            email=email,
            hashed_password=auth.get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            role="passenger"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"Successfully created user {email} with ID {new_user.id}")
        
        # Cleanup
        db.delete(new_user)
        db.commit()
        print("Test user deleted.")
    except Exception as e:
        print(f"Registration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_registration()
