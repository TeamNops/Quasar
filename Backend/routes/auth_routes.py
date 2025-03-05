from fastapi import APIRouter, HTTPException, status, Depends, Header
from datetime import datetime, timedelta
import hashlib
import jwt
from pymongo.errors import DuplicateKeyError
from database import get_db
from models.user_models import UserRegistration, UserLogin
from jwt_config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(user_id: str):
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegistration):
    db = get_db()
    users_collection = db.users
    profiles_collection = db.user_profiles
    
    # Check if user already exists
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user data
    user_data = {
        "email": user.email,
        "password_hash": hash_password(user.password),
        "registration_date": datetime.utcnow(),
        "last_login": None,
        "status": "active",
    }
    
    # Insert user and get the ID
    user_result = users_collection.insert_one(user_data)
    user_id = user_result.inserted_id
    
    # Create profile data if first_name is provided
    if hasattr(user, 'first_name') and user.first_name:
        profile_data = {
            "user_id": user_id,
            "first_name": user.first_name,
            "last_name": user.last_name if hasattr(user, 'last_name') else None,
            "location": user.location if hasattr(user, 'location') else None,
            "role": user.role if hasattr(user, 'role') else None,
        }
        profiles_collection.insert_one(profile_data)
    
    # Generate JWT token
    access_token = create_access_token(str(user_id))
    
    return {
        "id": str(user_id), 
        "message": "User registered successfully",
        "token": access_token,
        "onboarding_complete": False
    }

@router.post("/login")
async def login(credentials: UserLogin):
    db = get_db()
    users_collection = db.users
    hashed_pw = hash_password(credentials.password)
    user = users_collection.find_one({"email": credentials.email, "password_hash": hashed_pw})
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update the last_login timestamp
    users_collection.update_one(
        {"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Generate JWT token
    access_token = create_access_token(str(user["_id"]))
    
    # Get onboarding status
    onboarding_complete = user.get("onboarding_complete", False)
    
    return {
        "message": "User logged in successfully", 
        "user_id": str(user["_id"]),
        "token": access_token,
        "onboarding_complete": onboarding_complete
    }