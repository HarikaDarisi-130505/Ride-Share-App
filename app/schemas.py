from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    vehicle_details: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    role: str
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    vehicle_details: Optional[str] = None
    is_verified: bool = False
    driver_verified: bool = False
    driver_verified_at: Optional[datetime] = None
    two_factor_enabled: bool = False
    rides_given: int = 0
    rides_taken: int = 0
    rating_avg: float = 0.0
    total_ratings: int = 0
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    
    class Config:
        from_attributes = True

# Login Schemas
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginOTPRequest(BaseModel):
    email: str
    otp: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TwoFactorUpdateRequest(BaseModel):
    enabled: bool

class DriverVerificationResponse(BaseModel):
    driver_verified: bool
    driver_verified_at: Optional[datetime] = None
    message: str

class RegisterRequest(BaseModel):
    name: str # Mapped to full_name
    email: str
    password: str
    phone_number: str

# Ride Schemas
class CheckpointCreate(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    stop_order: int

class CheckpointBase(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    stop_order: int

    class Config:
        from_attributes = True

class RideBase(BaseModel):
    origin: Optional[str] = "Unknown"
    destination: Optional[str] = "Unknown"
    departure_time: datetime
    seats_available: int
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    price: Optional[float] = None
    route_polyline: Optional[str] = None
    preferences: Optional[str] = None
    comfort_mode: Optional[bool] = False
    women_only: Optional[bool] = False
    instant_booking: Optional[bool] = False
    stop_prices: Optional[str] = None  # JSON string

class RideCreate(RideBase):
    checkpoints: List[CheckpointCreate] = []

class Ride(RideBase):
    id: int
    creator_id: int
    status: Optional[str] = "scheduled"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    suggested_price: Optional[float] = None
    creator: Optional[User] = None
    checkpoints: List[CheckpointBase] = []
    
    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    ride_id: int

class Booking(BookingBase):
    id: int
    user_id: int
    booked_at: datetime
    ride: Optional[Ride] = None
    
    class Config:
        from_attributes = True

# Ride Request Schemas
class RideRequestBase(BaseModel):
    ride_id: int
    origin: Optional[str] = None
    destination: Optional[str] = None
    num_seats: int = 1

class RideRequestCreate(RideRequestBase):
    pass

class RideRequest(RideRequestBase):
    id: int
    passenger_id: int
    status: Optional[str] = "pending"
    requested_at: datetime
    ride: Optional[Ride] = None
    passenger: Optional[User] = None

    class Config:
        from_attributes = True

class MyRidesResponse(BaseModel):
    created: List[Ride]
    joined: List[Ride]

class ChatMessageBase(BaseModel):
    ride_id: int
    message: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    user_id: int
    timestamp: datetime
    user: Optional[User] = None
    
    class Config:
        from_attributes = True

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

class ParticipantLocation(BaseModel):
    user_id: int
    full_name: str
    latitude: Optional[float]
    longitude: Optional[float]
    last_update: Optional[datetime]
    role: str # 'driver' or 'passenger'

class RideLocations(BaseModel):
    driver: Optional[ParticipantLocation] = None
    passengers: List[ParticipantLocation] = []


class RideParticipant(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    role: str
    is_verified: bool = False
    driver_verified: bool = False
    driver_verified_at: Optional[datetime] = None
    rides_given: int = 0
    rides_taken: int = 0
    rating_avg: float = 0.0
    total_ratings: int = 0
    vehicle_details: Optional[str] = None

    class Config:
        from_attributes = True


class RideParticipantsResponse(BaseModel):
    driver: RideParticipant
    passengers: List[RideParticipant] = []

# Rating Schemas
class RatingBase(BaseModel):
    ride_id: int
    reviewee_id: int
    stars: int # 1-5
    comment: Optional[str] = None

class RatingCreate(RatingBase):
    pass

class Rating(RatingBase):
    id: int
    reviewer_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PendingRatingPrompt(BaseModel):
    ride_id: int
    reviewee_id: int
    reviewee_name: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    completed_at: Optional[datetime] = None

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class OTPVerifyResponse(BaseModel):
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[int] = None
    email: Optional[str] = None

class CancelRequest(BaseModel):
    reason: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
