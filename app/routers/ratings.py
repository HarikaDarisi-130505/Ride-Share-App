
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from .. import database, models, schemas, auth

router = APIRouter(
    prefix="/ratings",
    tags=["Ratings"]
)

@router.get("/pending", response_model=List[schemas.PendingRatingPrompt])
def get_pending_ratings(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    completed_bookings = (
        db.query(models.Booking)
        .options(
            joinedload(models.Booking.ride).joinedload(models.Ride.creator)
        )
        .join(models.Ride, models.Booking.ride_id == models.Ride.id)
        .filter(
            models.Booking.user_id == current_user.id,
            models.Ride.status == "completed"
        )
        .all()
    )

    pending_ratings = []
    for booking in completed_bookings:
        ride = booking.ride
        if not ride or not ride.creator_id:
            continue

        existing_rating = (
            db.query(models.Rating.id)
            .filter(
                models.Rating.ride_id == ride.id,
                models.Rating.reviewer_id == current_user.id,
                models.Rating.reviewee_id == ride.creator_id
            )
            .first()
        )
        if existing_rating:
            continue

        pending_ratings.append(
            schemas.PendingRatingPrompt(
                ride_id=ride.id,
                reviewee_id=ride.creator_id,
                reviewee_name=ride.creator.full_name if ride.creator else "Driver",
                origin=ride.origin,
                destination=ride.destination,
                completed_at=ride.completed_at
            )
        )

    pending_ratings.sort(
        key=lambda item: item.completed_at.timestamp() if item.completed_at else float(item.ride_id),
        reverse=True
    )
    return pending_ratings

@router.post("/", response_model=schemas.Rating)
def create_rating(
    rating: schemas.RatingCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify ride exists and is completed
    ride = db.query(models.Ride).filter(models.Ride.id == rating.ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.status != "completed":
        raise HTTPException(status_code=400, detail="Can only rate completed rides")
        
    # Only passengers who joined the ride can rate the driver.
    is_passenger = db.query(models.Booking).filter(
        models.Booking.ride_id == ride.id, 
        models.Booking.user_id == current_user.id
    ).first() is not None
    
    if not is_passenger:
        raise HTTPException(status_code=403, detail="Only passengers can rate the driver for this ride")

    if rating.reviewee_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot rate yourself")

    if ride.creator_id != rating.reviewee_id:
        raise HTTPException(status_code=400, detail="Passengers can only rate the driver for this ride")

    existing_rating = db.query(models.Rating).filter(
        models.Rating.ride_id == rating.ride_id,
        models.Rating.reviewer_id == current_user.id,
        models.Rating.reviewee_id == rating.reviewee_id
    ).first()
    if existing_rating:
        raise HTTPException(status_code=400, detail="You have already rated this participant for this ride")

    # Create rating
    db_rating = models.Rating(
        ride_id=rating.ride_id,
        reviewer_id=current_user.id,
        reviewee_id=rating.reviewee_id,
        stars=rating.stars,
        comment=rating.comment
    )
    db.add(db_rating)
    
    # Update reviewee's stats
    reviewee = db.query(models.User).filter(models.User.id == rating.reviewee_id).first()
    if reviewee:
        current_total = reviewee.rating_avg * reviewee.total_ratings
        reviewee.total_ratings += 1
        reviewee.rating_avg = (current_total + rating.stars) / reviewee.total_ratings
    
    db.commit()
    db.refresh(db_rating)
    return db_rating
