from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from .. import database, models, schemas, auth

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.get("/{ride_id}", response_model=List[schemas.ChatMessage])
def get_chat_history(ride_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Verify user is driver or a passenger of this ride
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    # Check if participant
    is_driver = ride.creator_id == current_user.id
    is_passenger = db.query(models.Booking).filter(models.Booking.ride_id == ride_id, models.Booking.user_id == current_user.id).first() is not None
    has_request = db.query(models.RideRequest).filter(models.RideRequest.ride_id == ride_id, models.RideRequest.passenger_id == current_user.id).first() is not None
    
    # Allow access if participant OR if the ride is open for inquiries
    # In a real app, we might distinguish between public Q&A and private booking chat.
    # For now, we allow access to the chat room for anyone interested in the ride.
    if not (is_driver or is_passenger or has_request):
        if ride.status not in ["active", "scheduled"]:
            raise HTTPException(status_code=403, detail="Chat is only available for active or scheduled rides")

    messages = db.query(models.ChatMessage).options(joinedload(models.ChatMessage.user)).filter(
        models.ChatMessage.ride_id == ride_id
    ).order_by(models.ChatMessage.timestamp).all()
    return messages

@router.post("/", response_model=schemas.ChatMessage)
def send_message(
    message: schemas.ChatMessageCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_message = models.ChatMessage(
        ride_id=message.ride_id,
        user_id=current_user.id,
        message=message.message
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Refresh to get the user relationship for the response
    return db.query(models.ChatMessage).options(joinedload(models.ChatMessage.user)).filter(models.ChatMessage.id == new_message.id).first()
