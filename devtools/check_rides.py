from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app import models

db = SessionLocal()
rides = db.query(models.Ride).all()

print(f"Total rides found: {len(rides)}")
for ride in rides:
    print(f"ID: {ride.id}, Origin: {ride.origin}, Destination: {ride.destination}, Time: {ride.departure_time}, Status: {ride.status}, Seats: {ride.seats_available}")

db.close()
