from bson import ObjectId
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
        "first_name": user.first_name,
        "last_name": user.last_name if hasattr(user, 'last_name') else None,
        "location": user.location if hasattr(user, 'location') else None,
        "role": user.role if hasattr(user, 'role') else None,
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

@router.post("/update-onboarding-status")
async def update_onboarding_status(
    status: dict,
    authorization: str = Header(None)
):
    # Check for the Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract the token
    token = authorization.split(" ")[1]
    
    try:
        # Decode the token to get user_id
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        # Convert user_id string to ObjectId
        from bson import ObjectId
        user_id = ObjectId(user_id)
        
        # Update the user's onboarding status
        db = get_db()
        users_collection = db.users
        
        update_result = users_collection.update_one(
            {"_id": user_id},
            {"$set": {"onboarding_complete": status.get("onboarding_complete", True)}}
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Onboarding status updated successfully"}
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

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
    
    # Get onboarding status and assessment status
    onboarding_complete = user.get("onboarding_complete", False)
    assessment_complete = user.get("assessment_complete", False)
    
    return {
        "message": "User logged in successfully", 
        "user_id": str(user["_id"]),
        "token": access_token,
        "onboarding_complete": onboarding_complete,
        "assessment_complete": assessment_complete
    }

@router.get("/user-profile")
async def get_user_profile(authorization: str = Header(None)):
    # Check for the Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract the token
    token = authorization.split(" ")[1]
    
    try:
        # Decode the token to get user_id
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        # Convert user_id string to ObjectId
        user_id_obj = ObjectId(user_id)
        
        # Get the user data
        db = get_db()
        users_collection = db.users
        profiles_collection = db.user_profiles
        
        # First try to get from profiles collection for richer data
        user_profile = profiles_collection.find_one({"user_id": user_id_obj})
        
        # If no profile exists, get basic data from users collection
        if not user_profile:
            user = users_collection.find_one({"_id": user_id_obj})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
                
            return {
                "id": user_id,
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "firstName": user.get("first_name"),
                "lastName": user.get("last_name"),
                "email": user.get("email"),
                "location": user.get("location"),
                "role": user.get("role"),
                "joinedDate": user.get("registration_date").strftime("%B %Y") if user.get("registration_date") else None,
                "lastActive": user.get("last_login").strftime("%Y-%m-%d %H:%M:%S") if user.get("last_login") else None,
                "onboardingComplete": user.get("onboarding_complete", False),
                "assessmentComplete": user.get("assessment_complete", False)
            }
        
        # Return enriched profile data
        user = users_collection.find_one({"_id": user_id_obj})
        
        return {
            "id": user_id,
            "name": f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip(),
            "firstName": user_profile.get("first_name"),
            "lastName": user_profile.get("last_name"),
            "email": user.get("email") if user else None,
            "location": user_profile.get("location"),
            "role": user_profile.get("role"),
            "bio": user_profile.get("bio"),
            "skills": user_profile.get("skills", []),
            "joinedDate": user.get("registration_date").strftime("%B %Y") if user and user.get("registration_date") else None,
            "lastActive": user.get("last_login").strftime("%Y-%m-%d %H:%M:%S") if user and user.get("last_login") else "Today",
            "onboardingComplete": user.get("onboarding_complete", False) if user else False,
            "assessmentComplete": user.get("assessment_complete", False) if user else False
        }
            
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user data: {str(e)}")
    
# Add this to your auth_routes.py file

@router.post("/update-assessment-status")
async def update_assessment_status(
    status: dict,
    authorization: str = Header(None)
):
    # Check for the Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract the token
    token = authorization.split(" ")[1]
    
    try:
        # Decode the token to get user_id
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        # Convert user_id string to ObjectId if needed
        from bson import ObjectId
        user_id = ObjectId(user_id)
        
        # Update the user's assessment status
        db = get_db()
        users_collection = db.users
        
        update_result = users_collection.update_one(
            {"_id": user_id},
            {"$set": {"assessment_complete": status.get("assessment_complete", True)}}
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Assessment status updated successfully"}
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
@router.get("/login-activity")
async def get_login_activity(authorization: str = Header(None)):
    """Get user's login activity for the past week"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    
    try:
        # Decode the token to get user_id
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get login history for the past week
        db = get_db()
        
        # Get current date and date from 7 days ago
        today = datetime.utcnow()
        past_week = today - timedelta(days=7)
        
        # Find login records for this user in the past week
        login_logs = list(db.login_logs.find({
            "user_id": ObjectId(user_id),
            "login_time": {"$gte": past_week}
        }).sort("login_time", -1))
        
        # Format the response
        days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        activity_by_day = {day: 0 for day in days_of_week}
        
        # Count logins by day of week
        for log in login_logs:
            day_of_week = days_of_week[log["login_time"].weekday()]
            activity_by_day[day_of_week] += 1
        
        # Convert to array format expected by the frontend
        weekly_activity = []
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            # Convert raw count to a percentage (max 100%)
            percentage = min(100, activity_by_day[day] * 20)  # Each login = 20% of bar height
            weekly_activity.append({
                "day": day,
                "count": activity_by_day[day],
                "percentage": percentage
            })
        
        return {"weekly_activity": weekly_activity}
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    