from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app import models

db = SessionLocal()

# Nominatim Coordinates for Pamuru and Vijayawada
p_lat, p_lng = 15.898448, 80.6188452
v_lat, v_lng = 16.5115306, 80.6160469

# Create a test ride departing in 5 hours
departure = datetime.utcnow() + timedelta(hours=5)

# JSON path for route_polyline
path_data = [
    {"latitude": p_lat, "longitude": p_lng},
    {"latitude": v_lat, "longitude": v_lng}
]
mock_polyline = json.dumps(path_data)

new_ride = models.Ride(
    origin="Pamuru, Andhra Pradesh",
    destination="Vijayawada, Andhra Pradesh",
    origin_lat=p_lat,
    origin_lng=p_lng,
    destination_lat=v_lat,
    destination_lng=v_lng,
    departure_time=departure,
    seats_available=4,
    creator_id=1, # Nithish
    price=250.0,
    route_polyline=mock_polyline,
    status="active"
)

db.add(new_ride)
db.commit()
db.refresh(new_ride)

print(f"Created Test Ride ID: {new_ride.id} departing at {new_ride.departure_time}")
db.close()
