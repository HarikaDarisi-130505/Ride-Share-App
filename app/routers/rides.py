from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
from .. import database, models, schemas, auth

import math
import json
import polyline


def haversine_distance(lat1, lon1, lat2, lon2):
    radius_km = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def decode_route_points(polyline_str: str):
    if not polyline_str:
        return []

    try:
        if polyline_str.startswith("["):
            path = json.loads(polyline_str)
            return [(p["latitude"], p["longitude"]) for p in path]
        return polyline.decode(polyline_str)
    except Exception:
        return []


def build_route_cumulative_distances(route_points):
    cumulative = [0.0]
    for idx in range(1, len(route_points)):
        prev_lat, prev_lng = route_points[idx - 1]
        lat, lng = route_points[idx]
        cumulative.append(
            cumulative[-1] + haversine_distance(prev_lat, prev_lng, lat, lng)
        )
    return cumulative


def nearest_point_index(route_points, latitude, longitude):
    best_index = -1
    best_distance = float("inf")

    for idx, (lat, lng) in enumerate(route_points):
        distance = haversine_distance(latitude, longitude, lat, lng)
        if distance < best_distance:
            best_distance = distance
            best_index = idx

    return best_index, best_distance


def parse_stop_prices(stop_prices_raw):
    if not stop_prices_raw:
        return []

    try:
        parsed = json.loads(stop_prices_raw)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        return []

    return []


def build_route_nodes(ride, route_points):
    route_nodes = [
        {
            "name": ride.origin,
            "latitude": ride.origin_lat,
            "longitude": ride.origin_lng,
            "node_type": "origin",
            "stop_order": 0,
        }
    ]

    for checkpoint in sorted(ride.checkpoints, key=lambda cp: cp.stop_order):
        route_nodes.append(
            {
                "name": checkpoint.address,
                "latitude": checkpoint.latitude,
                "longitude": checkpoint.longitude,
                "node_type": "checkpoint",
                "stop_order": checkpoint.stop_order,
            }
        )

    route_nodes.append(
        {
            "name": ride.destination,
            "latitude": ride.destination_lat,
            "longitude": ride.destination_lng,
            "node_type": "destination",
            "stop_order": len(route_nodes),
        }
    )

    if not route_points:
        for idx, node in enumerate(route_nodes):
            node["point_index"] = idx
            node["distance_to_route_km"] = 0.0
        return route_nodes

    for node in route_nodes:
        point_index, distance_to_route_km = nearest_point_index(
            route_points, node["latitude"], node["longitude"]
        )
        node["point_index"] = point_index
        node["distance_to_route_km"] = distance_to_route_km

    route_nodes.sort(key=lambda node: (node["point_index"], node["stop_order"]))
    return route_nodes


def find_matching_route_segment(ride, pickup_lat, pickup_lng, dest_lat, dest_lng, threshold_km=5.0):
    route_points = decode_route_points(ride.route_polyline)
    route_nodes = build_route_nodes(ride, route_points)

    pickup_match_index = None
    pickup_match_distance = float("inf")
    dest_match_index = None
    dest_match_distance = float("inf")

    for index, node in enumerate(route_nodes):
        pickup_distance = haversine_distance(
            pickup_lat, pickup_lng, node["latitude"], node["longitude"]
        )
        if pickup_distance <= threshold_km and pickup_distance < pickup_match_distance:
            pickup_match_index = index
            pickup_match_distance = pickup_distance

        dest_distance = haversine_distance(
            dest_lat, dest_lng, node["latitude"], node["longitude"]
        )
        if dest_distance <= threshold_km and dest_distance < dest_match_distance:
            dest_match_index = index
            dest_match_distance = dest_distance

    if (
        pickup_match_index is not None
        and dest_match_index is not None
        and dest_match_index > pickup_match_index
    ):
        return {
            "pickup_index": pickup_match_index,
            "dest_index": dest_match_index,
            "route_nodes": route_nodes,
        }

    return None


def calculate_segment_based_price(ride, pickup_lat, pickup_lng, dest_lat, dest_lng):
    route_points = decode_route_points(ride.route_polyline)
    if len(route_points) < 2:
        return ride.price

    cumulative = build_route_cumulative_distances(route_points)
    if not cumulative or cumulative[-1] <= 0:
        return ride.price

    pickup_idx, _pickup_distance_km = nearest_point_index(route_points, pickup_lat, pickup_lng)
    dest_idx, _dest_distance_km = nearest_point_index(route_points, dest_lat, dest_lng)

    if pickup_idx == -1 or dest_idx == -1 or dest_idx <= pickup_idx:
        return ride.price

    pickup_cum = cumulative[pickup_idx]
    dest_cum = cumulative[dest_idx]
    trip_distance_km = max(0.1, dest_cum - pickup_cum)

    route_nodes = build_route_nodes(ride, route_points)
    stop_prices = parse_stop_prices(ride.stop_prices)

    matched_segment = find_matching_route_segment(
        ride, pickup_lat, pickup_lng, dest_lat, dest_lng
    )

    if matched_segment and stop_prices and len(stop_prices) == max(0, len(route_nodes) - 1):
        segment_total = 0.0
        for price_entry in stop_prices[
            matched_segment["pickup_index"]:matched_segment["dest_index"]
        ]:
            segment_total += float(price_entry.get("price", 0) or 0)
        if segment_total > 0:
            return round(segment_total, 2)

    if stop_prices and len(stop_prices) == max(0, len(route_nodes) - 1):
        pickup_node = None
        dest_node = None

        for index, node in enumerate(route_nodes):
            if node["distance_to_route_km"] <= 1.5:
                node_cum = cumulative[node["point_index"]]
                if abs(node_cum - pickup_cum) <= 1.5:
                    pickup_node = index
                if abs(node_cum - dest_cum) <= 1.5:
                    dest_node = index

        if pickup_node is not None and dest_node is not None and dest_node > pickup_node:
            segment_total = 0.0
            for price_entry in stop_prices[pickup_node:dest_node]:
                segment_total += float(price_entry.get("price", 0) or 0)
            if segment_total > 0:
                return round(segment_total, 2)

    total_price = float(ride.price or 0)
    if total_price <= 0:
        return ride.price

    total_route_km = cumulative[-1]
    ratio = min(1.0, trip_distance_km / total_route_km)
    return round(total_price * ratio, 2)

router = APIRouter(
    prefix="/rides",
    tags=["Rides"]
)

@router.get("/my-rides", response_model=schemas.MyRidesResponse)
def get_my_rides(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    try:
        created_rides = db.query(models.Ride).filter(models.Ride.creator_id == current_user.id).all()
        
        bookings = db.query(models.Booking).options(joinedload(models.Booking.ride)).filter(models.Booking.user_id == current_user.id).all()
        joined_rides = [booking.ride for booking in bookings if booking.ride is not None]
        
        return {"created": created_rides, "joined": joined_rides}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=schemas.Ride)
def create_ride(ride: schemas.RideCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    try:
        ride_data = ride.dict()
        checkpoints_data = ride_data.pop("checkpoints", [])

        if current_user.role != "driver":
            current_user.role = "driver"
        
        db_ride = models.Ride(**ride_data, creator_id=current_user.id, status="scheduled")
        db.add(db_ride)
        db.commit()
        db.refresh(db_ride)
        
        for cp in checkpoints_data:
            db_cp = models.Checkpoint(**cp, ride_id=db_ride.id)
            db.add(db_cp)
        
        if checkpoints_data:
            db.commit()
            db.refresh(db_ride)
            
        return db_ride
    except Exception as e:
        import traceback
        print("CREATE RIDE ERROR TRACEBACK:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/", response_model=List[schemas.Ride])
def get_rides(
    skip: int = 0, 
    limit: int = 100, 
    destination: str = None, 
    pickup_lat: float = None,
    pickup_lng: float = None,
    dest_lat: float = None,
    dest_lng: float = None,
    num_seats: int = 1,
    date: str = None,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        now = datetime.utcnow()
        query = db.query(models.Ride).options(
            joinedload(models.Ride.creator),
            joinedload(models.Ride.checkpoints)
        ).filter(
            models.Ride.status == "scheduled",
            models.Ride.seats_available >= num_seats,
            models.Ride.creator_id != current_user.id
        )


        if date:
            try:
                # Filter for rides on OR AFTER the selected date
                filter_date = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), datetime.min.time())
                query = query.filter(models.Ride.departure_time >= filter_date)
            except ValueError:
                query = query.filter(models.Ride.departure_time >= now)
        else:
            query = query.filter(models.Ride.departure_time >= now)

        # Order by departure time to show the closest rides first
        query = query.order_by(models.Ride.departure_time.asc())
        
        # 1. Basic Text Filter (only if coordinates NOT provided)
        if destination and not (pickup_lat and pickup_lng and dest_lat and dest_lng):
            query = query.filter(models.Ride.destination.ilike(f"%{destination}%"))
            
        rides = query.all()
        
        # 2. Smart Match Filter (if coordinates provided)
        if pickup_lat and pickup_lng and dest_lat and dest_lng:
            from ..services import matching
            filtered_rides = []
            for ride in rides:
                matched_segment = find_matching_route_segment(
                    ride,
                    pickup_lat,
                    pickup_lng,
                    dest_lat,
                    dest_lng,
                )

                if matched_segment or matching.smart_match(
                    (pickup_lat, pickup_lng), 
                    (dest_lat, dest_lng), 
                    ride.route_polyline
                ):
                    ride.suggested_price = calculate_segment_based_price(
                        ride,
                        pickup_lat,
                        pickup_lng,
                        dest_lat,
                        dest_lng,
                    )
                        
                    filtered_rides.append(ride)
            return filtered_rides[skip : skip + limit]

        # For non-smart search, suggested_price is just the base price
        for ride in rides:
            ride.suggested_price = ride.price
            
        return rides[skip : skip + limit]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ride_id}", response_model=schemas.Ride)
def get_ride(ride_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    ride = db.query(models.Ride).options(
        joinedload(models.Ride.creator),
        joinedload(models.Ride.checkpoints)
    ).filter(models.Ride.id == ride_id).first()
    
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    return ride


@router.get("/{ride_id}/participants", response_model=schemas.RideParticipantsResponse)
def get_ride_participants(
    ride_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ride = db.query(models.Ride).options(
        joinedload(models.Ride.creator),
        joinedload(models.Ride.bookings).joinedload(models.Booking.user)
    ).filter(models.Ride.id == ride_id).first()

    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    passengers = []
    seen_user_ids = set()

    for booking in ride.bookings:
        if booking.user and booking.user.id not in seen_user_ids:
            seen_user_ids.add(booking.user.id)
            passengers.append(booking.user)

    return {
        "driver": ride.creator,
        "passengers": passengers
    }

@router.post("/{ride_id}/join", response_model=schemas.Booking)
def join_ride(ride_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.seats_available <= 0:
        raise HTTPException(status_code=400, detail="No seats available")
        
    # Check if already booked
    existing_booking = db.query(models.Booking).filter(
        models.Booking.ride_id == ride_id,
        models.Booking.user_id == current_user.id
    ).first()
    if existing_booking:
        raise HTTPException(status_code=400, detail="You have already joined this ride")

    # Create Booking
    booking = models.Booking(user_id=current_user.id, ride_id=ride_id)
    db.add(booking)
    
    # Update seats
    ride.seats_available -= 1
    db.commit()
    db.refresh(booking)
    
    db.commit()
    db.refresh(booking)
    
    return booking


@router.post("/updates/location")
def update_location(
    location: schemas.LocationUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.current_lat = location.latitude
    current_user.current_lng = location.longitude
    current_user.last_location_update = datetime.utcnow()
    db.commit()
    return {"status": "success"}

@router.get("/location/{ride_id}", response_model=schemas.RideLocations)
def get_ride_locations(
    ride_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    driver = ride.creator
    locations = schemas.RideLocations()
    
    # Driver location
    locations.driver = {
        "user_id": driver.id,
        "full_name": driver.full_name,
        "latitude": driver.current_lat,
        "longitude": driver.current_lng,
        "last_update": driver.last_location_update,
        "role": "driver"
    }

    passenger_map = {}

    # Joined/booked passengers should always be visible to the driver after ride start.
    booked_passengers = db.query(models.User).join(
        models.Booking, models.Booking.user_id == models.User.id
    ).filter(
        models.Booking.ride_id == ride_id
    ).all()

    for passenger in booked_passengers:
        passenger_map[passenger.id] = passenger

    # Include active requesters too, so pending/accepted users can still be seen where relevant.
    requested_passengers = db.query(models.User).join(
        models.RideRequest, models.RideRequest.passenger_id == models.User.id
    ).filter(
        models.RideRequest.ride_id == ride_id,
        models.RideRequest.status.in_(["pending", "accepted", "confirmed"])
    ).all()

    for passenger in requested_passengers:
        passenger_map[passenger.id] = passenger

    for passenger in passenger_map.values():
        # Driver sees everyone. A passenger only sees themselves plus the driver.
        if current_user.id == driver.id or current_user.id == passenger.id:
            locations.passengers.append({
                "user_id": passenger.id,
                "full_name": passenger.full_name,
                "latitude": passenger.current_lat,
                "longitude": passenger.current_lng,
                "last_update": passenger.last_location_update,
                "role": "passenger"
            })
            
    return locations

@router.put("/{ride_id}/start", response_model=schemas.Ride)
def start_ride(
    ride_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the driver can start the ride")
        
    ride.status = "ongoing"
    ride.started_at = datetime.utcnow()
    db.commit()
    db.refresh(ride)
    return ride

@router.put("/{ride_id}/complete", response_model=schemas.Ride)
def complete_ride(
    ride_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the driver can complete the ride")
        
    ride.status = "completed"
    ride.completed_at = datetime.utcnow()
    
    # Increment driver rides_given
    ride.creator.rides_given += 1
    
    # Increment all booked passengers rides_taken
    for booking in ride.bookings:
        if booking.user:
            booking.user.rides_taken += 1
            
    db.commit()
    db.refresh(ride)
    return ride
@router.put("/{ride_id}/cancel", response_model=schemas.Ride)
def cancel_ride(
    ride_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the driver can cancel the ride")
        
    ride.status = "cancelled"
    
    # Also cancel all pending/accepted/confirmed requests for this ride
    db.query(models.RideRequest).filter(
        models.RideRequest.ride_id == ride_id,
        models.RideRequest.status.in_(["pending", "accepted", "confirmed"])
    ).update({"status": "cancelled"}, synchronize_session=False)
            
    # Delete all bookings for this ride
    db.query(models.Booking).filter(models.Booking.ride_id == ride_id).delete()
            
    db.commit()
    db.refresh(ride)
    return ride
@router.get("/search/smart", response_model=List[schemas.Ride])
def smart_search_rides(
    pickup_lat: float,
    pickup_lng: float,
    dest_lat: float,
    dest_lng: float,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        now = datetime.utcnow()
        active_rides = db.query(models.Ride).filter(
            models.Ride.status == "scheduled",
            models.Ride.departure_time >= now,
            models.Ride.creator_id != current_user.id
        ).all()

        
        from ..services import matching
        matches = []
        for ride in active_rides:
            if matching.smart_match(
                (pickup_lat, pickup_lng), 
                (dest_lat, dest_lng), 
                ride.route_polyline
            ):
                matches.append(ride)
        
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
