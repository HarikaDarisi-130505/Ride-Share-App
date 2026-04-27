from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from .. import models, schemas, database, auth

router = APIRouter(
    prefix="/requests",
    tags=["requests"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.RideRequest)
def create_ride_request(
    request: schemas.RideRequestCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify Ride exists
    ride = db.query(models.Ride).filter(models.Ride.id == request.ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    if request.num_seats <= 0:
        raise HTTPException(status_code=400, detail="Requested seats must be greater than zero")
        
    if request.num_seats > ride.seats_available:
        raise HTTPException(status_code=400, detail=f"Only {ride.seats_available} seats available")
        
    # Check if passenger already has an active request FOR THIS RIDE
    existing_for_ride = db.query(models.RideRequest).filter(
        models.RideRequest.passenger_id == current_user.id,
        models.RideRequest.ride_id == request.ride_id,
        models.RideRequest.status.in_(["pending", "accepted", "confirmed"])
    ).first()
    if existing_for_ride:
        raise HTTPException(status_code=400, detail="You have already requested or joined this ride.")


    # Resolve Origin and Destination (fallback to Ride defaults if missing)
    origin = request.origin if request.origin else ride.origin
    destination = request.destination if request.destination else ride.destination

    new_request = models.RideRequest(
        passenger_id=current_user.id,
        ride_id=request.ride_id,
        origin=origin,
        destination=destination,
        num_seats=request.num_seats,
        status="pending"
    )
    db.add(new_request)
    
    # Auto-accept if instant booking is on
    if getattr(ride, 'instant_booking', False):
        new_request.status = "confirmed"
        booking = models.Booking(user_id=current_user.id, ride_id=ride.id)
        db.add(booking)
        ride.seats_available -= request.num_seats

    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/driver", response_model=List[schemas.RideRequest])
def get_driver_requests(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get all ride requests for the current user's (driver's) published rides."""
    return db.query(models.RideRequest).options(
        joinedload(models.RideRequest.ride).joinedload(models.Ride.creator),
        joinedload(models.RideRequest.passenger)
    ).join(models.Ride).filter(
        models.Ride.creator_id == current_user.id,
        models.RideRequest.status == "pending"
    ).all()

@router.get("/passenger", response_model=List[schemas.RideRequest])
def get_passenger_requests(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get all ride requests made by the current user (passenger)."""
    return db.query(models.RideRequest).options(
        joinedload(models.RideRequest.ride).joinedload(models.Ride.creator)
    ).filter(
        models.RideRequest.passenger_id == current_user.id
    ).all()

@router.get("/", response_model=List[schemas.RideRequest])
def get_all_my_requests(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Combined view for backward compatibility or general list
    passenger_requests = db.query(models.RideRequest).options(
        joinedload(models.RideRequest.ride).joinedload(models.Ride.creator)
    ).filter(
        models.RideRequest.passenger_id == current_user.id
    ).all()
    
    driver_requests = db.query(models.RideRequest).options(
        joinedload(models.RideRequest.ride).joinedload(models.Ride.creator),
        joinedload(models.RideRequest.passenger)
    ).join(models.Ride).filter(
        models.Ride.creator_id == current_user.id
    ).all()
    
    return list({r.id: r for r in (passenger_requests + driver_requests)}.values())

@router.put("/{request_id}/accept", response_model=schemas.RideRequest)
def accept_request(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ride_request = db.query(models.RideRequest).filter(models.RideRequest.id == request_id).first()
    if not ride_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    ride = ride_request.ride
    if ride.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this request")
        
    if ride.seats_available < ride_request.num_seats:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough seats available (Requested: {ride_request.num_seats}, Available: {ride.seats_available})"
        )
        
    # Transaction
    try:
        # 1. Update Request Status
        ride_request.status = "accepted"
        
        # 2. Decrement Seats immediately upon acceptance so others see updated count
        ride.seats_available -= ride_request.num_seats
        
        db.commit()
        db.refresh(ride_request)
        return ride_request
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{request_id}/confirm", response_model=schemas.RideRequest)
def confirm_request(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Passenger confirms the accepted request"""
    ride_request = db.query(models.RideRequest).filter(models.RideRequest.id == request_id).first()
    if not ride_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if ride_request.passenger_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to confirm this request")
        
    if ride_request.status != "accepted":
        raise HTTPException(status_code=400, detail="Request must be accepted by driver first")
        
    ride = ride_request.ride
    # If already booked, just ensure the request status is updated and return success
    existing_booking = db.query(models.Booking).filter(
        models.Booking.ride_id == ride.id,
        models.Booking.user_id == current_user.id
    ).first()
    
    if existing_booking:
        ride_request.status = "confirmed"
        db.commit()
        db.refresh(ride_request)
        return ride_request

        
    # Transaction
    try:
        # 1. Update Request Status to 'confirmed'
        ride_request.status = "confirmed"
        
        # 2. Create Booking
        booking = models.Booking(user_id=ride_request.passenger_id, ride_id=ride.id)
        db.add(booking)
        
        # NOTE: Seats were already decremented during accept_request
        
        db.commit()
        db.refresh(ride_request)
        return ride_request
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{request_id}/reject", response_model=schemas.RideRequest)
def reject_request(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ride_request = db.query(models.RideRequest).filter(models.RideRequest.id == request_id).first()
    if not ride_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    ride = ride_request.ride
    if ride.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to reject this request")
        
    if ride_request.status in ["accepted", "confirmed"]:
        ride.seats_available += ride_request.num_seats

    ride_request.status = "rejected"
    db.commit()
    db.refresh(ride_request)
    return ride_request

@router.get("/status/{ride_id}", response_model=Optional[schemas.RideRequest])
def get_ride_request_status(
    ride_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    request = db.query(models.RideRequest).options(joinedload(models.RideRequest.ride)).filter(
        models.RideRequest.ride_id == ride_id,
        models.RideRequest.passenger_id == current_user.id
    ).order_by(models.RideRequest.requested_at.desc()).first()
    return request

@router.put("/{request_id}/cancel", response_model=schemas.RideRequest)
def cancel_request(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    request = db.query(models.RideRequest).filter(models.RideRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.passenger_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your request")
    
    if request.status in ["accepted", "confirmed"]:
        # Return the seats to the ride if it was already accepted or confirmed
        ride = request.ride
        if ride:
            ride.seats_available += request.num_seats
            # Delete Booking
            db.query(models.Booking).filter(
                models.Booking.user_id == request.passenger_id,
                models.Booking.ride_id == request.ride_id
            ).delete()
            
    request.status = "cancelled"
    db.commit()
    db.refresh(request)
    return request
