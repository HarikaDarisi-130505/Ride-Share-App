import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app import models

def inspect_rides():
    db = SessionLocal()
    try:
        rides = db.query(models.Ride).all()
        print(f"Total rides: {len(rides)}")
        for ride in rides:
            print(f"ID: {ride.id}, From: '{ride.origin}', To: '{ride.destination}'")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_rides()
