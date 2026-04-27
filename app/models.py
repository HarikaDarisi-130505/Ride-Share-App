from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default="passenger") # passenger, driver, admin
    phone_number = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True) # male, female, other, unspecified
    date_of_birth = Column(DateTime, nullable=True)
    vehicle_details = Column(String(500), nullable=True) # JSON string: {model, color, plate}
    is_verified = Column(Boolean, default=False)
    driver_verified = Column(Boolean, default=False)
    driver_verified_at = Column(DateTime, nullable=True)
    two_factor_enabled = Column(Boolean, default=False)
    
    # Rating Stats
    rating_avg = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    rides_given = Column(Integer, default=0)
    rides_taken = Column(Integer, default=0)
    
    # Live Tracking Fields
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)

    rides_created = relationship("Ride", back_populates="creator")

class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String(255), index=True)
    destination = Column(String(255), index=True)
    departure_time = Column(DateTime)
    seats_available = Column(Integer)
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    # New Fields for Route Matching and Pricing
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    route_polyline = Column(LONGTEXT) # Stores encoded polyline for long routes
    preferences = Column(String(500), nullable=True) # JSON string for preferences
    comfort_mode = Column(Boolean, default=False)  # Max 2 in back
    women_only = Column(Boolean, default=False)
    instant_booking = Column(Boolean, default=False)
    stop_prices = Column(LONGTEXT, nullable=True)  # JSON array of segment prices
    status = Column(String(50), default="scheduled") # scheduled, active, in_progress, completed, cancelled
    
    # Ride Lifecycle Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    creator = relationship("User", back_populates="rides_created")
    bookings = relationship("Booking", back_populates="ride")
    checkpoints = relationship("Checkpoint", back_populates="ride")
    requests = relationship("RideRequest", back_populates="ride")

class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(255))
    stop_order = Column(Integer)

    ride = relationship("Ride", back_populates="checkpoints")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ride_id = Column(Integer, ForeignKey("rides.id"))
    booked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    ride = relationship("Ride", back_populates="bookings")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class RideRequest(Base):
    __tablename__ = "ride_requests"

    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(Integer, ForeignKey("users.id"))
    ride_id = Column(Integer, ForeignKey("rides.id")) # Link to specific ride
    origin = Column(String(255))
    destination = Column(String(255))
    status = Column(String(50), default="pending") # pending, accepted, rejected, cancelled, expired
    num_seats = Column(Integer, default=1)
    requested_at = Column(DateTime, default=datetime.utcnow)

    passenger = relationship("User", back_populates="ride_requests")
    ride = relationship("Ride", back_populates="requests")

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewee_id = Column(Integer, ForeignKey("users.id"))
    stars = Column(Integer, default=5) # 1-5
    comment = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ride = relationship("Ride")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviewee = relationship("User", foreign_keys=[reviewee_id])

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True)
    otp = Column(String(6))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_verified = Column(Boolean, default=False)

# Update User to include bookings and requests
User.bookings = relationship("Booking", back_populates="user")
User.ride_requests = relationship("RideRequest", back_populates="passenger")

