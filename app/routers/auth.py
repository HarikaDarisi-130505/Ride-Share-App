from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import datetime
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth
from ..services import email_service
import random
import json
from pathlib import Path

# Authentication Router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def build_user_profile(db: Session, user: models.User) -> schemas.User:
    rides_given = db.query(models.Ride).filter(models.Ride.creator_id == user.id).count()
    rides_taken = db.query(models.Booking).filter(models.Booking.user_id == user.id).count()

    user_data = schemas.User.from_orm(user)
    user_data.rides_given = rides_given
    user_data.rides_taken = rides_taken
    return user_data


def log_otp(email: str, otp: str, expires_at: datetime.datetime, otp_type: str):
    print(f"\n[{otp_type}] For {email}: {otp}")
    try:
        log_path = Path(__file__).resolve().parents[2] / "otp_log.txt"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(
                f"TYPE: {otp_type}\n"
                f"EMAIL: {email}\n"
                f"CODE: {otp}\n"
                f"EXPIRES: {expires_at}\n"
                "------------------------------\n"
            )
    except Exception:
        pass

# Original Token Endpoint (Optional, kept for reference or OAuth2 standard tools)
@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# New Login Endpoint (JSON Body)
@router.post("/login")
def login(request: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    try:
        email = request.email.lower().strip()
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user or not auth.verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        if user.two_factor_enabled:
            otp = str(random.randint(100000, 999999))
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

            otp_entry = models.OTPVerification(
                email=email,
                otp=otp,
                expires_at=expires_at
            )
            db.add(otp_entry)
            db.commit()

            log_otp(email, otp, expires_at, "LOGIN_2FA")
            email_service.send_otp_email(email, otp, type="login_2fa")

            return {
                "message": "OTP sent to your email",
                "requires_two_factor": True,
                "email": user.email
            }

        # Generate Tokens
        access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = auth.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = auth.create_refresh_token(
            data={"sub": user.email}, expires_delta=refresh_token_expires
        )
        
        return {
            "message": "Login successful",
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "phone_number": user.phone_number,
            "is_verified": user.is_verified,
            "driver_verified": user.driver_verified,
            "driver_verified_at": user.driver_verified_at,
            "rating_avg": user.rating_avg,
            "total_ratings": user.total_ratings,
            "two_factor_enabled": user.two_factor_enabled,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        print("LOGIN ERROR TRACEBACK:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/verify-login-otp")
def verify_login_otp(request: schemas.LoginOTPRequest, db: Session = Depends(database.get_db)):
    email = request.email.lower().strip()
    otp_entry = db.query(models.OTPVerification).filter(
        models.OTPVerification.email == email,
        models.OTPVerification.otp == request.otp,
        models.OTPVerification.is_verified == False
    ).order_by(models.OTPVerification.created_at.desc()).first()

    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    if otp_entry.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP code has expired")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_entry.is_verified = True
    db.commit()

    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = datetime.timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = auth.create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    return {
        "message": "Login successful",
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "phone_number": user.phone_number,
        "is_verified": user.is_verified,
        "driver_verified": user.driver_verified,
        "driver_verified_at": user.driver_verified_at,
        "rating_avg": user.rating_avg,
        "total_ratings": user.total_ratings,
        "two_factor_enabled": user.two_factor_enabled,
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(request: schemas.RefreshTokenRequest, db: Session = Depends(database.get_db)):
    try:
        user = auth.verify_refresh_token(request.refresh_token, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        
        access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": request.refresh_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Refresh Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, please login again"
        )

# New Register Endpoint
@router.post("/register")
def register(request: schemas.RegisterRequest, db: Session = Depends(database.get_db)):
    try:
        email = request.email.lower().strip()
        db_user = db.query(models.User).filter(models.User.email == email).first()
        
        if db_user:
            if db_user.is_verified:
                raise HTTPException(status_code=400, detail="Email already registered")
            else:
                # User exists but not verified - update their info to allow re-registration
                db_user.full_name = request.name
                db_user.phone_number = request.phone_number
                db_user.hashed_password = auth.get_password_hash(request.password)
                db.commit()
                db.refresh(db_user)
                new_user = db_user
        else:
            # Create new user
            hashed_password = auth.get_password_hash(request.password)
            new_user = models.User(
                email=email, 
                hashed_password=hashed_password, 
                full_name=request.name,
                phone_number=request.phone_number,
                is_verified=False
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        
        # OTP Logic (SQL-Based)
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        
        otp_entry = models.OTPVerification(
            email=email,
            otp=otp,
            expires_at=expires_at
        )
        db.add(otp_entry)
        db.commit()
        
        log_otp(email, otp, expires_at, "REGISTER")
        email_service.send_otp_email(email, otp)
        
        return {
            "message": "User registered successfully. Please verify your email.",
            "requires_verification": True,
            "email": request.email
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        print("REGISTER ERROR TRACEBACK:")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/verify-otp")
def verify_otp(request: schemas.OTPVerifyRequest, db: Session = Depends(database.get_db)):
    # Check in database
    otp_entry = db.query(models.OTPVerification).filter(
        models.OTPVerification.email == request.email,
        models.OTPVerification.otp == request.otp,
        models.OTPVerification.is_verified == False
    ).order_by(models.OTPVerification.created_at.desc()).first()
    
    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    # Check expiry
    if otp_entry.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP code has expired")
    
    # Mark OTP as verified
    otp_entry.is_verified = True
    
    # Update User as verified
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if user:
        user.is_verified = True
        db.commit()
        db.refresh(user)
        
        # Create tokens
        access_token = auth.create_access_token(data={"sub": user.email})
        refresh_token = auth.create_refresh_token(data={"sub": user.email})
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/me", response_model=schemas.User)
def read_users_me(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        return build_user_profile(db, current_user)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/me", response_model=schemas.User)
def update_user_me(
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name
        if user_update.phone_number is not None:
            current_user.phone_number = user_update.phone_number
        if user_update.vehicle_details is not None:
            current_user.vehicle_details = user_update.vehicle_details
        if user_update.gender is not None:
            current_user.gender = user_update.gender
        if user_update.date_of_birth is not None:
            current_user.date_of_birth = user_update.date_of_birth
        
        db.commit()
        db.refresh(current_user)

        return build_user_profile(db, current_user)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/driver-verification", response_model=schemas.DriverVerificationResponse)
def verify_driver_profile(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "driver":
        current_user.role = "driver"

    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="Complete account verification first")

    if not current_user.phone_number:
        raise HTTPException(status_code=400, detail="Add a phone number before verification")

    vehicle = {}
    try:
        vehicle = json.loads(current_user.vehicle_details or "{}")
    except Exception:
        vehicle = {}

    if not vehicle.get("model") or not vehicle.get("color") or not vehicle.get("plate"):
        raise HTTPException(status_code=400, detail="Please complete your vehicle details before verification")

    current_user.driver_verified = True
    current_user.driver_verified_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return {
        "driver_verified": current_user.driver_verified,
        "driver_verified_at": current_user.driver_verified_at,
        "message": "Driver profile verified successfully"
    }


@router.post("/change-password")
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")

    if auth.verify_password(request.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="New password must be different from the current password")

    current_user.hashed_password = auth.get_password_hash(request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.put("/two-factor")
def update_two_factor(
    request: schemas.TwoFactorUpdateRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.two_factor_enabled = request.enabled
    db.commit()
    db.refresh(current_user)

    return {
        "message": f"Two-factor authentication {'enabled' if request.enabled else 'disabled'} successfully",
        "two_factor_enabled": current_user.two_factor_enabled
    }

@router.post("/forgot-password")
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(database.get_db)):
    email = request.email.lower().strip()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # For security, don't reveal if user exists or not, 
        # but in a campus app, it's often better to be helpful.
        raise HTTPException(status_code=404, detail="No account found with this email")
    
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    
    otp_entry = models.OTPVerification(
        email=email,
        otp=otp,
        expires_at=expires_at
    )
    db.add(otp_entry)
    db.commit()
    
    log_otp(email, otp, expires_at, "PASSWORD_RESET")
    email_service.send_otp_email(email, otp, type="password_reset")
        
    return {"message": "OTP sent to your email for password reset"}

@router.post("/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(database.get_db)):
    # Verify OTP
    email = request.email.lower().strip()
    otp_entry = db.query(models.OTPVerification).filter(
        models.OTPVerification.email == email,
        models.OTPVerification.otp == request.otp,
        models.OTPVerification.is_verified == False
    ).order_by(models.OTPVerification.created_at.desc()).first()
    
    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    if otp_entry.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP code has expired")
    
    # Update Password
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = auth.get_password_hash(request.new_password)
    otp_entry.is_verified = True
    db.commit()
    
    return {"message": "Password reset successfully. You can now login with your new password."}
